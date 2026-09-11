"""An unchanged brief must expose content lost from a reconstructed map."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw
import pytest
from slidepoise.reconstruction.coverage import content_obligation_errors


def case():
    entities = [{"id": "draft", "kind": "icon"}, {"id": "review", "kind": "icon"},
                {"id": "caption", "kind": "text"},
                {"id": "feedback", "kind": "connector", "connector_intent": {
                    "source_entities": ["review"], "target_entities": ["draft"], "directed": True}}]
    handoff = {"content_obligations": [{"id": "rejection", "description": "Review returns rejected work to drafting",
        "entity_ids": ["caption", "feedback"], "connection": {"entity_id": "feedback",
            "source_entities": ["review"], "target_entities": ["draft"], "directed": True}}]}
    return entities, handoff


def test_feedback_caption_cannot_replace_its_connection():
    entities, handoff = case()
    assert content_obligation_errors(entities, handoff) == []
    errors = content_obligation_errors(entities[:-1], handoff)
    assert {e["reason"] for e in errors} >= {"required_content_entity_missing", "required_connection_missing"}


@pytest.mark.parametrize("mutation", ["reverse", "undirected", "owner_missing", "nonmeaningful"])
def test_changed_relationship_fails_the_independent_obligation(mutation):
    entities, handoff = case()
    if mutation == "reverse":
        entities[-1]["connector_intent"].update(source_entities=["draft"], target_entities=["review"])
    elif mutation == "undirected":
        entities[-1]["connector_intent"]["directed"] = False
    elif mutation == "owner_missing":
        entities.pop(0)
    else:
        entities[-1]["meaningful_visible"] = False
    assert content_obligation_errors(entities, handoff)


def test_constructor_checks_obligations_before_building_objects():
    from slidepoise.reconstruction.contract import build_reconstruction_contract
    entities, handoff = case()
    with pytest.raises(ValueError, match="Unfulfilled content obligations"):
        build_reconstruction_contract({"entities": entities[:-1], "upstream_handoff": handoff}, {})


@pytest.mark.parametrize("significance", ["owned_content", "measurement_evidence", "non_authoritative_glyph"])
def test_required_arrow_cannot_be_satisfied_by_its_caption(significance):
    from slidepoise.reconstruction.contract import build_reconstruction_contract
    entities, handoff = case()
    entities[-1].update(reconstruction_significance=significance, render_owner="caption")
    with pytest.raises(ValueError, match="required_connection_must_emit_geometry"):
        build_reconstruction_contract({"entities": entities, "upstream_handoff": handoff}, {})


def test_measured_group_endpoints_compile_without_becoming_content_entities(tmp_path):
    from slidepoise.reconstruction.contract import build_reconstruction_contract

    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "framework/defaults/slidepoise-config.json").read_text())
    config["design"]["full_slide_px"] = [1000, 500]
    for name in ("header", "footer"):
        config["design"]["frame"][name]["enabled"] = False
    target = Image.new("RGB", (1000, 500), "white")
    draw = ImageDraw.Draw(target)
    entities = []
    groups = []
    for name, x in (("draft", 50), ("review", 650)):
        draw.rectangle((x + 20, 120, x + 220, 200), fill="#DDDDDD")
        entities.append({"id": name, "kind": "shape", "shape": "rectangle", "z": 10,
                         "bbox_hint": [x + 20, 120, 200, 80], "geometry_policy": "agent_logical",
                         "style_hint": {"fill": "#DDDDDD", "stroke": "none"}})
        groups.append({"id": name + "-group", "bbox_hint": [x, 100, 250, 120], "children": [name]})
    draw.line((300, 160, 650, 160), fill="black", width=2)
    entities.append({"id": "flow", "kind": "connector", "bbox_hint": [300, 150, 350, 20], "z": 20,
                     "connector_intent": {"source_entities": ["draft-group"], "target_entities": ["review-group"],
                         "connector_family": "direct_flow", "directed": True,
                         "source_attachment_sides": ["right"], "target_attachment_sides": ["left"],
                         "source_attachment_fractions": [0.5], "target_attachment_fractions": [0.5],
                         "semantic_topology_verified": True, "visual_route_reviewed": True,
                         "visual_route_decision": "The clear horizontal corridor connects the two stage groups.",
                         "route_mode": "minimal_orthogonal", "junction_style": "none"},
                     "visual_constraints": {"arrowhead_treatment": "open_arrow_at_target"}})
    handoff = {"content_obligations": [{"id": "flow", "description": "Drafting proceeds to review",
        "entity_ids": ["flow"], "connection": {"entity_id": "flow", "source_entities": ["draft-group"],
            "target_entities": ["review-group"], "directed": True}}]}
    target.save(tmp_path / "target.png")
    for name, value in (("config", config), ("semantic", {"entities": entities, "groups": groups}), ("handoff", handoff)):
        (tmp_path / (name + ".json")).write_text(json.dumps(value))
    result = subprocess.run([sys.executable, str(root / "slidepoise/scripts/slidepoise_runtime.py"),
        "reconstruct-slide", "--image", str(tmp_path / "target.png"), "--config", str(tmp_path / "config.json"),
        "--semantic-map", str(tmp_path / "semantic.json"), "--upstream-handoff", str(tmp_path / "handoff.json"),
        "--slide-id", "group-flow", "--output-dir", str(tmp_path / "reconstruction")],
        text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    scene = json.loads((tmp_path / "reconstruction/constructor-scene.json").read_text())
    connector = next(item for item in scene["objects"] if item["id"] == "flow")
    # Ports belong to the enclosing groups, not the smaller visible children.
    assert connector["target_routes_px"] == [[[300.0, 160.0], [650.0, 160.0]]]
    measured = json.loads((tmp_path / "reconstruction/measurement/slide_entities.json").read_text())
    missing = deepcopy(measured)
    missing["groups"].pop()
    with pytest.raises(ValueError, match="required_connection_owner_missing"):
        build_reconstruction_contract(missing, config["design"])

    # Group endpoints must have real descendants. Nested groups are supported,
    # but empty groups, dangling members and cycles cannot cover a relation.
    nested = deepcopy(measured)
    nested["groups"][0]["children"] = ["draft-inner"]
    nested["groups"].append({"id": "draft-inner", "children": ["draft"]})
    build_reconstruction_contract(nested, config["design"])
    for children in ([], ["missing-child"], ["draft-group"]):
        broken = deepcopy(nested)
        broken["groups"][-1]["children"] = children
        with pytest.raises(ValueError, match="required_connection_group_invalid"):
            build_reconstruction_contract(broken, config["design"])

    ordinary = deepcopy(measured)
    ordinary["upstream_handoff"]["content_obligations"][0]["entity_ids"].append("draft-group")
    with pytest.raises(ValueError, match="required_content_entity_missing"):
        build_reconstruction_contract(ordinary, config["design"])
