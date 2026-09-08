"""Frozen examples rebuild with repository resources despite user customization."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def test_example_rebuild_isolated_from_installed_library_sets(tmp_path):
    example = tmp_path / "example"
    work = example / "run/slides/opening/work"
    work.mkdir(parents=True)
    (example / "run/work").mkdir()
    (example / "run/work/deck-outline.json").write_text(json.dumps({
        "title": "A reproducible example", "slides": [{"slide_id": "opening"}]}))
    (example / "run/session-overrides.json").write_text(json.dumps({
        "profile": "consulting", "header": {"enabled": False}, "footer": {"enabled": False}}))
    shared_design = example / "run/work/deck-design.json"
    shared_design.write_text(json.dumps({"schema_version": "1.0", "design_id": "example-editorial-identity",
                                        "repeated_roles": {"series_marker": {"chosen_style": {"font_family": "Arial", "font_size_pt": 12}}}}))
    image = Image.new("RGB", (1600, 900), "white")
    ImageDraw.Draw(image).text((100, 100), "Reviewable output", fill="black")
    image.save(work / "accepted-slide.png")
    (work / "semantic-map.json").write_text(json.dumps({"schema_version": "3.2.0", "entities": [{
        "id": "headline", "display_label": "Reviewable output", "kind": "text", "text": "Reviewable output",
        "text_style_role": "slide_title", "typography_group": "headline", "bbox_hint": [100, 100, 800, 100],
        "geometry_policy": "agent_logical", "meaningful_visible": True, "z": 10,
        "style_hint": {"font_family": "Arial", "target_font_size_px": 48}}]}))
    (work / "reconstruction-handoff.json").write_text(json.dumps({"selected_assets": [],
        "deck_design_source": {"path": "../../../work/deck-design.json", "sha256": hashlib.sha256(shared_design.read_bytes()).hexdigest()},
        "recurring_role_bindings": [{"role_id": "series_marker", "entity_ids": ["headline"], "typography_group": "headline"}]}))
    # A real installed catalog without the example's sets would break resolution
    # if this rebuild accidentally consumed the contributor's personal home.
    poisoned = tmp_path / "installed-home/library-sets"
    poisoned.mkdir(parents=True)
    (poisoned / "catalog.json").write_text(json.dumps({"items": {}}))
    output = tmp_path / "rebuilt"
    result = subprocess.run([sys.executable, str(ROOT / "examples/rebuild.py"), str(example),
                             "--output-dir", str(output), "--no-preview"], cwd=tmp_path,
                            env={**os.environ, "SLIDEPOISE_HOME": str(poisoned.parent)}, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    config = json.loads((output / "work/resolved-config.json").read_text())
    assert Path(config["library_sets"]["root"]) == ROOT / "library-sets"
    receipt = json.loads((output / "rebuild.json").read_text())
    assert receipt["slide_ids"] == ["opening"]
    for entry in receipt["input_files"]:
        assert entry["sha256"] == hashlib.sha256((example / entry["path"]).read_bytes()).hexdigest()
    with zipfile.ZipFile(output / receipt["presentation"]) as package:
        assert "Reviewable output" in package.read("ppt/slides/slide1.xml").decode()
    assert (output / receipt["portable_manifest"]).is_file()
    assert not list(tmp_path.glob(".slidepoise-rebuild-*"))
    # Resolve the exact retained relative binding after publication removed the
    # temporary path. The decision is useful only if the handoff still finds it.
    rebuilt_handoff = output / "slides/opening/work/reconstruction-handoff.json"
    design_binding = json.loads(rebuilt_handoff.read_text())["deck_design_source"]
    copied_design = (rebuilt_handoff.parent / design_binding["path"]).resolve()
    assert copied_design == output / "work/deck-design.json"
    assert copied_design.read_bytes() == shared_design.read_bytes()
    assert hashlib.sha256(copied_design.read_bytes()).hexdigest() == design_binding["sha256"]
    assert json.loads(rebuilt_handoff.read_text())["recurring_role_bindings"][0]["entity_ids"] == ["headline"]

    # An abandoned edit may remain in the authoring history. Reusing the
    # original must work even when the rejected asset no longer exists.
    semantic_path = work / "semantic-map.json"
    semantic = json.loads(semantic_path.read_text())
    semantic["entities"].append({
        "id": "artwork", "kind": "image", "bbox_hint": [100, 350, 300, 300], "z": 1,
        "geometry_policy": "agent_logical", "visual_source_class": "novel_illustration",
        "raster_source_override": str(tmp_path / "discarded-art.png"),
        "raster_decision": {"action": "reuse_original", "reviewed_by": "host_agent_visual_reasoning",
                            "reason": "The original preserves the intended artwork."},
    })
    semantic_path.write_text(json.dumps(semantic))
    fallback = subprocess.run([sys.executable, str(ROOT / "examples/rebuild.py"), str(example),
                               "--output-dir", str(tmp_path / "fallback"), "--no-preview"],
                              cwd=tmp_path, text=True, capture_output=True)
    assert fallback.returncode == 0, fallback.stdout + fallback.stderr
    assert (tmp_path / "fallback/bundle/deck-scenes.json").is_file()

    # A changed shared choice cannot silently reuse an earlier handoff binding.
    shared_design.write_text(shared_design.read_text() + "\n")
    stale_output = tmp_path / "stale-rebuild"
    stale = subprocess.run([sys.executable, str(ROOT / "examples/rebuild.py"), str(example),
                            "--output-dir", str(stale_output), "--no-preview"], cwd=tmp_path,
                           text=True, capture_output=True)
    assert stale.returncode != 0
    assert "Stale or missing shared deck design" in stale.stderr
    assert not stale_output.exists()
    assert not list(tmp_path.glob(".slidepoise-rebuild-*"))
