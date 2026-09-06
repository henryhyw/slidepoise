"""Release evidence respects content owned by native charts and missing text."""

import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "slidepoise/scripts"))

from collect_release_evidence import typography_checks


def native_chart_and_caption():
    semantic = {"entities": [
        {"id": "caption", "kind": "text", "typography_group": "labels"},
        {"id": "chart-value", "kind": "text", "typography_group": "labels"},
    ]}
    contract = {"reconstruction_units": [
        {"id": "caption", "emits_ppt_object": True},
        {"id": "chart-value", "emits_ppt_object": False, "render_owner": "chart"},
    ]}
    scene = {"objects": [
        {"id": "caption", "kind": "textbox", "style": {"font_size_pt": 16}},
        {"id": "chart", "kind": "chart"},
    ], "compiler_report": {"text_fitting": {"text_groups": [
        {"typography_group": "labels", "member_ids": ["caption"], "shared_font_size_pt": 16},
    ]}}}
    return semantic, contract, scene


def test_chart_owned_values_need_no_duplicate_textbox_or_peer_fit():
    semantic, contract, scene = native_chart_and_caption()
    original = copy.deepcopy((semantic, contract, scene))
    assert typography_checks(semantic, contract, scene) == []
    assert (semantic, contract, scene) == original


def test_owned_value_exclusion_cannot_hide_missing_native_caption():
    semantic, contract, scene = native_chart_and_caption()
    scene["objects"] = [scene["objects"][1]]
    assert {"entity": "caption", "reason": "emitting_textbox_missing_from_scene"} in typography_checks(semantic, contract, scene)


def test_missing_contract_unit_cannot_silently_exclude_text_from_evidence():
    semantic, contract, scene = native_chart_and_caption()
    contract["reconstruction_units"] = contract["reconstruction_units"][1:]
    assert {"entity": "caption", "reason": "release_text_missing_reconstruction_unit"} in typography_checks(semantic, contract, scene)
