"""Fine artwork stays bound to the source through fetch and reconstruction."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))
sys.path.insert(0, str(ROOT / "slidepoise/runtime/src"))

import fetch_remix_icon_pair as fetcher
from collect_semantic_evidence import remix_icon_variant_errors
from prepare_resource_context import prepare_generation_previews
from slidepoise.icon_geometry import IconGeometryError, fine_remix_svg
from slidepoise.reconstruction.contract import build_reconstruction_contract
from slidepoise.reconstruction.scene import build_reconstruction_scene

RING = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M2 2H22V22H2Z M4 4V20H20V4Z"/></svg>'
FILL = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M2 2H22V22H2Z"/></svg>'


def mock_source(monkeypatch, category="Document"):
    monkeypatch.setattr(fetcher, "locate_pair", lambda name, version: {
        variant: f"icons/{category}/{name}-{variant}.svg" for variant in ("line", "fill")
    })
    monkeypatch.setattr(fetcher, "request", lambda url: RING if url.endswith("-line.svg") else FILL)


def test_fine_reduces_ink_preserves_extent_and_repeats_exactly():
    svg, facts = fine_remix_svg(RING)
    assert fine_remix_svg(RING) == (svg, facts)
    assert facts["source_geometry"]["bounds"] == facts["derived_geometry"]["bounds"] == [2, 2, 22, 22]
    assert facts["derived_geometry"]["ink_area"] < facts["source_geometry"]["ink_area"]
    assert facts["derived_geometry"]["enclosed_holes"] == 1
    assert facts["restore_visible_extent_scale"] == pytest.approx(20 / 19.3)
    assert facts["inset_source_units"] == 0.35
    assert facts["engines"]["shapely"]


def test_fill_rules_are_honoured_before_offset():
    same_direction = RING.replace(b"M4 4V20H20V4Z", b"M4 4H20V20H4Z")
    _, nonzero = fine_remix_svg(same_direction)
    _, evenodd = fine_remix_svg(same_direction.replace(b"<path", b'<path fill-rule="evenodd"'))
    assert nonzero["source_geometry"]["enclosed_holes"] == 0
    assert evenodd["source_geometry"]["enclosed_holes"] == 1


@pytest.mark.parametrize("source", [
    RING.replace(b"<path", b'<path transform="scale(2)"'),
    RING.replace(b"<path", b'<path fill="red"'),
    RING.replace(b"0 0 24 24", b"0 0 48 48"),
    RING.replace(b"M2 2H22V22H2Z M4 4V20H20V4Z", b"M2 2H2.2V2.2H2Z"),
])
def test_unsupported_or_erased_geometry_requires_explicit_choice(source):
    with pytest.raises(IconGeometryError):
        fine_remix_svg(source)


def test_fetch_default_retains_original_and_never_double_thins(monkeypatch, tmp_path):
    mock_source(monkeypatch)
    pair = fetcher.fetch_pair("test", "4.9.0", tmp_path)
    line, fill = pair["candidates"]
    assert pair["line_weight"] == "fine"
    assert line["asset_id"] == "remix-test-line-fine"
    assert Path(line["source_file"]).read_bytes() == RING
    assert line["source_sha256"] == hashlib.sha256(RING).hexdigest()
    assert line["sha256"] == hashlib.sha256(Path(line["canonical_file"]).read_bytes()).hexdigest()
    assert line["sha256"] != line["source_sha256"]
    assert Path(fill["canonical_file"]).read_bytes() == FILL
    again = fetcher.fetch_pair("test", "4.9.0", tmp_path)
    assert again["candidates"][0]["sha256"] == line["sha256"]


@pytest.mark.parametrize("category,weight", [("Document", "original"), ("Logos", "fine")])
def test_original_override_and_logos_preserve_official_bytes(monkeypatch, tmp_path, category, weight):
    mock_source(monkeypatch, category)
    pair = fetcher.fetch_pair("test", "4.9.0", tmp_path, line_weight=weight)
    assert pair["line_weight"] == "original"
    assert all(asset["canonical_file"] == asset["source_file"] for asset in pair["candidates"])
    assert Path(pair["candidates"][0]["canonical_file"]).read_bytes() == RING


def test_fine_asset_is_used_for_generation_and_reconstruction(monkeypatch, tmp_path):
    mock_source(monkeypatch)
    pair = fetcher.fetch_pair("test", "4.9.0", tmp_path)
    resources = {"selected_assets": pair["candidates"]}
    prepare_generation_previews(resources, tmp_path / "previews")
    line = resources["selected_assets"][0]
    assert line["generation_preview"]["source"] == {"path": line["canonical_file"], "sha256": line["sha256"]}
    design = {"full_slide_px": [1600, 900], "profile_hard_rules": {"icons": {"proxy_treatments": [{"id": "ink", "glyph": "#223344"}]}}}
    measured = {"source": {"width_px": 1600, "height_px": 900}, "upstream_handoff": resources, "entities": [{
        "id": "test", "kind": "icon", "z": 1, "reconstruction_route": "canonical_asset",
        "upstream_asset_id": line["asset_id"], "icon_treatment_group": "peers", "icon_treatment": "ink",
        "style_hint": {"icon_inset_fraction": 0}, "measurement": {"layout_bbox": {"px": [40, 40, 48, 48]}},
    }]}
    contract = build_reconstruction_contract(measured, design)
    mapping = contract["canonical_asset_mappings"][0]
    assert mapping["geometry_treatment"] == line["geometry_treatment"]
    assert mapping["upstream_source_sha256"] == line["source_sha256"]
    scene = build_reconstruction_scene(measured_scene=measured, contract=contract, design=design, slide_id="fine")
    assert scene["objects"][0]["source_path"] == line["canonical_file"]
    assert scene["objects"][0]["source_sha256"] == line["sha256"]
    assert scene["objects"][0]["recolor"] == "#223344"


@pytest.mark.parametrize("override,expected", [(None, "fine"), ("original", "original"), ("invalid", None)])
def test_legacy_config_default_and_session_override(tmp_path, override, expected):
    base = json.loads((ROOT / "framework/defaults/slidepoise-config.json").read_text())
    base["remote_sources"]["remix_icon"].pop("line_weight")
    (tmp_path / "base.json").write_text(json.dumps(base))
    (tmp_path / "session.json").write_text(json.dumps({"profile": "monochrome-modern", "remote_sources": {"remix_icon": {"line_weight": override}}}))
    output = tmp_path / "resolved.json"
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/resolve_config.py"),
        "--base", str(tmp_path / "base.json"), "--profiles-root", str(ROOT / "profiles"),
        "--session", str(tmp_path / "session.json"), "--output", str(output)], capture_output=True, text=True)
    if expected is None:
        assert result.returncode != 0
        assert "must be fine or original" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert json.loads(output.read_text())["remote_sources"]["remix_icon"]["line_weight"] == expected


def test_peer_weight_mixing_is_reported(monkeypatch, tmp_path):
    mock_source(monkeypatch)
    fine = fetcher.fetch_pair("test", "4.9.0", tmp_path)
    original = fetcher.fetch_pair("test", "4.9.0", tmp_path, line_weight="original")
    entities = [{"id": str(index), "kind": "icon", "upstream_asset_id": pair["candidates"][0]["asset_id"],
        "icon_variant": "line", "icon_treatment_group": "peers", "icon_variant_review": {
            "stage": "post_generation_visual_review", "reviewed_by": "host_agent_visual_reasoning",
            "evaluated_asset_ids": pair["candidates"][0]["pair_asset_ids"],
            "decision": "Readable at slide size.", "observations": ["The detail is visible."]}}
        for index, pair in enumerate([fine, original])]
    errors = remix_icon_variant_errors(entities, {"selected_assets": fine["candidates"] + original["candidates"]})
    assert "remix_icon_peer_group_mixes_line_weights" in {error["reason"] for error in errors}
