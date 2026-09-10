from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise" / "scripts"))
sys.path.insert(0, str(ROOT / "slidepoise" / "runtime" / "scripts"))
sys.path.insert(0, str(ROOT / "slidepoise" / "runtime" / "src"))

from measure_visual_scene import measured_layout_box, normalize_local_geometry
from raster_decisions import illustration_decision_errors, illustration_decisions
from collect_release_evidence import accepted_review
from slidepoise.reconstruction.scene import _apply_explicit_z_order, _connector_routes, _round_rect_adjustment, _transform_contours
from slidepoise.reconstruction.text_fit import _base_style, _wrap

HOST = "host_agent_visual_reasoning"


def measured_pair():
    return [{"id": key, "kind": "shape", "measurement": {"layout_bbox": {"px": box}}}
            for key, box in [("a", [10, 10, 30, 20]), ("b", [11, 60, 30, 20])]]


def test_measurement_does_not_snap_nearby_peers():
    measured = measured_pair()
    original = copy.deepcopy(measured)
    report = normalize_local_geometry(measured, {"entities": [{"id": "a", "kind": "shape"}, {"id": "b", "kind": "shape"}]}, {})
    assert measured == original
    assert report["adjustment_count"] == 0


def test_only_host_selected_position_changes():
    measured = measured_pair()
    decision = {"entity_id": "b", "before_bbox_px": [11, 60, 30, 20], "after_bbox_px": [10, 60, 30, 20], "reviewed_by": HOST, "reason": "The two panel left edges are intended to share one column."}
    report = normalize_local_geometry(measured, {"geometry_adjustments": [decision]}, {})
    assert measured[1]["measurement"]["layout_bbox"]["px"] == [10, 60, 30, 20]
    assert report["adjustment_count"] == 1
    assert measured[0]["measurement"]["layout_bbox"]["px"] == [10, 10, 30, 20]


def test_host_selected_correction_is_not_rejected_by_an_aesthetic_distance_cap():
    measured = measured_pair()
    decision = {"entity_id": "b", "before_bbox_px": [11, 60, 30, 20], "after_bbox_px": [40, 75, 30, 20], "reviewed_by": HOST, "reason": "The accepted target places this object in a different logical column."}
    report = normalize_local_geometry(measured, {"geometry_adjustments": [decision]}, {})
    assert measured[1]["measurement"]["layout_bbox"]["px"] == [40.0, 75.0, 30.0, 20.0]
    assert report["adjustment_count"] == 1


def test_stale_correction_fails_without_partial_mutation():
    measured = measured_pair()
    original = copy.deepcopy(measured)
    decisions = [
        {"entity_id": "a", "before_bbox_px": [10, 10, 30, 20], "after_bbox_px": [11, 10, 30, 20], "reviewed_by": HOST, "reason": "Reviewed edge correction."},
        {"entity_id": "b", "before_bbox_px": [12, 60, 30, 20], "after_bbox_px": [10, 60, 30, 20], "reviewed_by": HOST, "reason": "Stale edge correction."},
    ]
    with pytest.raises(ValueError, match="stale"):
        normalize_local_geometry(measured, {"geometry_adjustments": decisions}, {})
    assert measured == original


def raster(key="art", action="reuse_original"):
    return {"id": key, "kind": "image", "visual_source_class": "novel_illustration", "bbox_hint": [0, 0, 40, 40], "geometry_policy": "agent_logical", "raster_decision": {"action": action, "reviewed_by": HOST, "reason": "Crop inspected at intended export scale."}}


def test_reuse_needs_no_extra_image_call_approval():
    assert illustration_decision_errors({"entities": [raster()]}, {}) == []


def test_refinement_is_a_host_decision_independent_of_approval_tokens():
    semantic = {"entities": [raster(action="refine")]}
    assert not illustration_decision_errors(semantic, {})
    assert not illustration_decision_errors(semantic, {"illustrations": {"status": "pending", "entity_ids": []}})
    assert not illustration_decision_errors(semantic, {"illustrations": {"status": "approved", "entity_ids": ["art"]}})


def test_occluded_native_text_cannot_enter_isolated_refinement():
    entity = raster(action="refine")
    entity["raster_decision"]["occluding_native_text_ids"] = ["heading"]
    with pytest.raises(ValueError, match="occlusion"):
        illustration_decisions({"entities": [entity]})


def test_board_contains_only_selected_refinements(tmp_path):
    import subprocess
    source = tmp_path / "source.png"
    Image.new("RGB", (80, 80), "gray").save(source)
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps({"entities": [raster("keep"), raster("edit", "refine")]}))
    manifest = tmp_path / "manifest.json"
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/prepare_illustration_refinement.py"),
        "--image", str(source), "--semantic-map", str(semantic), "--config", str(ROOT / "framework/defaults/slidepoise-config.json"),
        "--output-dir", str(tmp_path / "crops"), "--board", str(tmp_path / "board.png"), "--review-board", str(tmp_path / "review.png"),
        "--manifest", str(manifest), "--brief", str(tmp_path / "brief.md")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert [item["entity_id"] for item in json.loads(manifest.read_text())["items"]] == ["edit"]
    assert not (tmp_path / "crops/source-crops/keep.png").exists()


def test_review_rejects_changed_render_and_missing_observations(tmp_path):
    artifact = tmp_path / "render.png"
    Image.new("RGB", (8, 8), "white").save(artifact)
    review = tmp_path / "review.json"
    record = {"reviewer": HOST, "stage": "reconstruction", "decision": "accepted", "material_issues": [], "observations": ["Test observation, no real slide acceptance."],
        "reviewed_artifacts": [{"path": "render.png", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}]}
    review.write_text(json.dumps(record))
    assert accepted_review(review, "reconstruction", (artifact,))[0]
    record["observations"] = []
    review.write_text(json.dumps(record))
    assert not accepted_review(review, "reconstruction", (artifact,))[0]
    record["observations"] = ["Test observation."]
    review.write_text(json.dumps(record))
    Image.new("RGB", (8, 8), "black").save(artifact)
    assert not accepted_review(review, "reconstruction", (artifact,))[0]


def test_personal_profile_preserves_observed_font_and_color():
    profile = json.loads((ROOT / "profiles/editorial-archive/profile.json").read_text())
    design = {**profile["design_overrides"], "profile_hard_rules": profile["hard_rules"]}
    entity = {"text_style_role": "label", "style_hint": {"font_family": "Courier New", "observed_foreground_color": "#504943", "style_authority": "agent_visual_observation", "italic": True}}
    style = _base_style(entity, design)
    assert style["family"] == "Courier New"
    assert style["color"] == "#504943"
    assert style["italic"]


def test_closed_profile_still_restricts_font_choice():
    design = {"style": {"display_font": "Georgia", "body_font": "Arial"}, "profile_hard_rules": {"typography": {"italics_allowed": False}}}
    style = _base_style({"style_hint": {"font_family": "Courier New", "italic": True}}, design)
    assert style["family"] == "Arial"
    assert not style["italic"]


def test_tracking_is_included_in_text_fit():
    from slidepoise.reconstruction.text_fit import _fits
    entity = {"text": "WIDE", "measurement": {"layout_bbox": {"px": [0, 0, 90, 30]}}}
    style = {"family": "Arial", "bold": False, "italic": False, "role_policy": {"inset_px": 0}}
    assert _fits(entity, style, 20) is not None
    assert _fits(entity, {**style, "char_spacing_px": 30}, 20) is None


def test_unspaced_cjk_text_gets_powerpoint_compatible_break_opportunities():
    from slidepoise.reconstruction.text_fit import _load_font

    text = "这是一段应当在文本框内正常换行且保持目标字号的中文文字"
    font = _load_font("Arial", False, False, 96)
    lines = _wrap(text, font, 360)
    assert len(lines) > 1
    assert "".join(lines) == text


def test_opencv_contours_follow_the_generation_region_transform():
    contours = [[[100, 50], [300, 50], [300, 250], [100, 250]]]
    assert _transform_contours(contours, [0.5, 0.75], 80) == [
        [[50.0, 117.5], [150.0, 117.5], [150.0, 267.5], [50.0, 267.5]]
    ]


def test_measurement_requires_agent_selected_geometry_authority():
    with pytest.raises(ValueError, match="geometry_policy"):
        measured_layout_box("shape", [10, 10, 40, 30], [11, 12, 37, 26], {"id": "panel"})
    entity = {"id": "panel", "geometry_policy": "opencv_visible"}
    assert measured_layout_box("shape", [10, 10, 40, 30], [11, 12, 37, 26], entity) == [11, 12, 37, 26]


def test_opencv_text_color_never_becomes_implicit_reconstruction_color():
    design = {"style": {"body_font": "Arial"}, "text_reconstruction": {"text_style_policies": {"default": {"color": "#222222"}}}}
    entity = {"style_hint": {"style_authority": "profile_policy"}, "measurement": {"text_color_evidence": {"foreground": "#FF00FF"}}}
    assert _base_style(entity, design)["color"] == "#222222"


def test_round_rect_uses_agent_observed_radius_without_aesthetic_cap():
    design = {"shape_geometry": {"rounding": {"intent_values": ["ordinary_container"]}}}
    radius, adjustment = _round_rect_adjustment(
        {"id": "card", "shape_intent": "ordinary_container", "corner_radius_px": 30},
        [0, 0, 200, 100],
        design,
        [1, 1],
    )
    assert radius == 30
    assert adjustment == 30000


def test_stacking_relation_validates_agent_z_without_rewriting_it():
    objects = [{"id": "paper", "z": 2}, {"id": "label", "z": 5}]
    _apply_explicit_z_order(objects, [{"back": "paper", "front": "label"}])
    assert objects == [{"id": "paper", "z": 2}, {"id": "label", "z": 5}]
    with pytest.raises(ValueError, match="conflict"):
        _apply_explicit_z_order(objects, [{"back": "label", "front": "paper"}])


def test_connector_compiler_requires_explicit_agent_route_delegation():
    plan = {
        "entity_id": "flow",
        "connector_family": "direct_flow",
        "source_attachment_sides": ["right"],
        "target_attachment_sides": ["left"],
        "route_visual_review": {"reviewed": True},
    }
    with pytest.raises(ValueError, match="route_mode"):
        _connector_routes(plan, [[100, 100]], [[300, 100]], [])
    plan["route_mode"] = "minimal_orthogonal"
    assert _connector_routes(plan, [[100, 100]], [[300, 100]], [])[1] == [[[100.0, 100.0], [300.0, 100.0]]]


def test_renderer_preserves_italic_tracking_and_open_cubic_path(tmp_path):
    import subprocess
    import zipfile
    import xml.etree.ElementTree as ET
    fixture = {"slide": {"dimensions_px": [1600, 900], "objects": [
        {"id": "editorial-text", "kind": "textbox", "bbox_px": [100, 100, 500, 80], "text": "Editorial", "style": {"font_family": "Times New Roman", "font_size_pt": 20, "italic": True, "char_spacing_px": 3}},
        {"id": "curved-path", "kind": "freeform", "bbox_px": [100, 300, 400, 100], "path_commands_px": [{"op": "M", "point": [100, 400]}, {"op": "C", "control1": [220, 300], "control2": [350, 300], "point": [500, 310]}], "style": {"fill": "none", "stroke": "#333333", "end_arrow_type": "arrow"}},
    ]}}
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(fixture))
    output = tmp_path / "spec.pptx"
    result = subprocess.run(["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        xml = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    props = xml.find(".//a:rPr", ns)
    assert props.get("i") == "1"
    assert int(props.get("spc")) > 0
    assert len(xml.findall(".//a:cubicBezTo", ns)) == 1
    assert not xml.findall(".//a:path/a:close", ns)


def test_renderer_emits_native_chart(tmp_path):
    import subprocess
    import zipfile

    fixture = {"slide": {"dimensions_px": [1600, 900], "objects": [
        {"id": "native-chart", "kind": "chart", "bbox_px": [120, 160, 560, 360], "z": 1,
         "structure": {"type": "bar", "categories": ["One", "Two"], "series": [{"name": "Value", "values": [3, 7]}]},
         "style": {"fill": "#FFFFFF", "stroke": "none"}},
    ]}}
    spec = tmp_path / "chart.json"
    spec.write_text(json.dumps(fixture), encoding="utf-8")
    output = tmp_path / "chart.pptx"
    result = subprocess.run(
        ["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        assert "ppt/charts/chart1.xml" in archive.namelist()


def test_visual_comparison_writes_raw_pixel_difference_evidence(tmp_path):
    import subprocess

    target = tmp_path / "target.png"
    render = tmp_path / "render.png"
    Image.new("RGB", (4, 3), "#102030").save(target)
    image = Image.new("RGB", (4, 3), "#102030")
    image.putpixel((2, 1), (20, 50, 40))
    image.save(render)
    comparison = tmp_path / "comparison.png"
    difference = tmp_path / "difference.png"
    result = subprocess.run(
        [sys.executable, str(ROOT / "slidepoise/scripts/make_visual_comparison.py"),
         "--left", str(target), "--right", str(render), "--output", str(comparison), "--difference", str(difference)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert Image.open(difference).getpixel((2, 1)) == (4, 18, 8)
    assert Image.open(difference).getpixel((0, 0)) == (0, 0, 0)
