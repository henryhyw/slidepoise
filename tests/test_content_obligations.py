"""An unchanged brief must expose content lost from a reconstructed map."""
from copy import deepcopy
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
