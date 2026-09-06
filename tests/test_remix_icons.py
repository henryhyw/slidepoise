from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))

import fetch_remix_icon_pair as fetcher
from make_semantic_explanation_overlay import render
from collect_semantic_evidence import remix_icon_variant_errors


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M1 1h22v22H1z"/></svg>'


def assets(tmp_path):
    pair = ["remix-brain-line", "remix-brain-fill"]
    return [
        {
            "asset_id": asset_id,
            "canonical_file": str(tmp_path / f"{asset_id}.svg"),
            "provider": "Remix Icon",
            "provider_version": "4.9.0",
            "style_variant": variant,
            "style_pair_id": "remix-brain",
            "pair_asset_ids": pair,
        }
        for asset_id, variant in zip(pair, ("line", "fill"))
    ]


def icon(identifier, asset_id, variant, group="peer-icons"):
    return {
        "id": identifier,
        "kind": "icon",
        "upstream_asset_id": asset_id,
        "icon_variant": variant,
        "icon_treatment_group": group,
        "icon_variant_review": {
            "stage": "post_generation_visual_review",
            "reviewed_by": "host_agent_visual_reasoning",
            "evaluated_asset_ids": ["remix-brain-line", "remix-brain-fill"],
            "decision": "Line weight best matches the approved slide.",
            "observations": ["The line silhouette stays legible and matches peer rules."],
        },
    }


def test_official_pair_lookup_retains_line_and_fill(monkeypatch):
    tree = {"truncated": False, "tree": [
        {"type": "blob", "path": "icons/Health & Medical/brain-line.svg"},
        {"type": "blob", "path": "icons/Health & Medical/brain-fill.svg"},
    ]}
    monkeypatch.setattr(fetcher, "request", lambda _url: json.dumps(tree).encode())
    assert fetcher.locate_pair("brain", "4.9.0") == {
        "line": "icons/Health & Medical/brain-line.svg",
        "fill": "icons/Health & Medical/brain-fill.svg",
    }
    assert fetcher.validate_svg(SVG) == [0.0, 0.0, 24.0, 24.0]


def test_post_generation_variant_review_accepts_one_consistent_peer_style(tmp_path):
    handoff = {"selected_assets": assets(tmp_path)}
    entities = [icon("a", "remix-brain-line", "line"), icon("b", "remix-brain-line", "line")]
    assert remix_icon_variant_errors(entities, handoff) == []


def test_post_generation_variant_review_rejects_mixed_peer_style(tmp_path):
    handoff = {"selected_assets": assets(tmp_path)}
    entities = [icon("a", "remix-brain-line", "line"), icon("b", "remix-brain-fill", "fill")]
    reasons = {item["reason"] for item in remix_icon_variant_errors(entities, handoff)}
    assert "remix_icon_peer_group_mixes_line_and_fill" in reasons


def test_variant_review_must_compare_both_candidates(tmp_path):
    handoff = {"selected_assets": assets(tmp_path)}
    entity = icon("a", "remix-brain-line", "line")
    entity["icon_variant_review"]["evaluated_asset_ids"] = ["remix-brain-line"]
    reasons = {item["reason"] for item in remix_icon_variant_errors([entity], handoff)}
    assert "remix_icon_variant_review_must_compare_both_pair_assets" in reasons


def test_semantic_explanation_overlay_uses_authored_groups_and_relationships(tmp_path):
    image = tmp_path / "slide.png"
    Image.new("RGB", (320, 180), "white").save(image)
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps({
        "entities": [
            {"id": "a", "kind": "shape", "role": "source", "bbox_hint": [20, 40, 70, 50]},
            {"id": "b", "kind": "shape", "role": "target", "bbox_hint": [220, 40, 70, 50]},
        ],
        "groups": [
            {"id": "g-a", "display_label": "Inputs", "semantic_class": "evidence group", "bbox_hint": [10, 25, 100, 90], "children": ["a"]},
            {"id": "g-b", "display_label": "Outcome", "semantic_class": "recommendation group", "bbox_hint": [210, 25, 100, 90], "children": ["b"]},
        ],
        "relationships": [{"id": "r", "type": "supports", "display_label": "supports", "source": "g-a", "target": "g-b"}],
    }))
    output = tmp_path / "overlay.png"
    report = render(image, semantic, output)
    assert report == {"output": str(output.resolve()), "entities": 2, "groups": 2, "relationships_rendered": 1, "notice": "Mechanical rendering of host-authored semantics. No semantic discovery or visual acceptance."}
    assert Image.open(output).size == (320, 180)
