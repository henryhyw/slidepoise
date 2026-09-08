"""Regression checks at reconstruction, native package, and persistence boundaries."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "slidepoise/runtime/src"), str(ROOT / "slidepoise/runtime/scripts"), str(ROOT / "slidepoise/scripts")]

from measure_visual_scene import clamp_box, get_box, normalize_local_geometry
from slidepoise.reconstruction.contract import build_reconstruction_contract
from slidepoise.reconstruction.scene import build_reconstruction_scene
from slidepoise.reconstruction.text_fit import _authored_text, _base_style, _wrap, _largest_size, finalize_fitted_text_entities
from framework import run_versions, storage
import package_self
import slidepoise_runtime

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}


class FixedMetrics:
    def getlength(self, text):
        return len(text) * 10


def test_mixed_cjk_copy_wraps_without_splitting_latin_words():
    text = "使用 OpenAI 构建清晰且可以编辑的演示文稿。"
    lines = _wrap(text, FixedMetrics(), 80)
    assert max(map(len, lines)) <= 8
    assert any("OpenAI" in line for line in lines)
    assert "".join(lines).replace(" ", "") == text.replace(" ", "")
    assert all(not line.startswith("。") for line in lines)


def test_authored_line_breaks_survive_by_default():
    assert _authored_text({"text": "First line\nSecond line"}) == "First line\nSecond line"
    assert _authored_text({"text": "First line\nSecond line", "preserve_explicit_breaks": False}) == "First line Second line"


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True])
def test_invalid_fitting_steps_fail_without_entering_search(value):
    with pytest.raises(ValueError, match="quantization_step_pt"):
        finalize_fitted_text_entities([], {}, {}, points_per_px=1, quantization_step_pt=value)


def test_owned_raster_lettering_does_not_participate_in_native_text_fitting():
    scene = {
        "source": {"width_px": 800, "height_px": 450, "path": "probe.png"},
        "entities": [
            {"id": "owner", "kind": "shape", "shape": "rectangle", "z": 0, "reconstruction_route": "native_shape", "measurement": {"layout_bbox": {"px": [20, 20, 300, 200]}}},
            {"id": "intrinsic", "kind": "text", "reconstruction_route": "native_text", "reconstruction_significance": "owned_content", "render_owner": "owner", "measurement": {"layout_bbox": {"px": [30, 30, 50, 20]}}},
        ],
    }
    design = {"full_slide_px": [800, 450], "frame": {"header": {"enabled": False}, "footer": {"enabled": False}}}
    contract = build_reconstruction_contract(scene, design)
    output = build_reconstruction_scene(measured_scene=scene, contract=contract, design=design, slide_id="probe")
    assert [obj["id"] for obj in output["objects"]] == ["owner"]
    assert output["compiler_report"]["text_fitting"]["fitted_textbox_count"] == 0


def test_missing_image_owner_fails_instead_of_disappearing():
    scene = {"source": {"width_px": 800, "height_px": 450}, "entities": [
        {"id": "art", "kind": "image", "z": 0, "reconstruction_route": "screenshot_crop", "measurement": {"layout_bbox": {"px": [20, 20, 300, 200]}}}
    ]}
    contract = build_reconstruction_contract(scene, {})
    with pytest.raises(ValueError, match="missing_emitting_entities"):
        build_reconstruction_scene(measured_scene=scene, contract=contract, design={}, slide_id="probe")


def test_clipping_is_an_intersection_and_corrections_respect_all_edges():
    assert clamp_box([-10, -5, 30, 20], 100, 100) == [0, 0, 20, 15]
    with pytest.raises(ValueError, match="no pixels"):
        clamp_box([150, 0, 20, 20], 100, 100)
    with pytest.raises(ValueError, match="finite"):
        get_box({"id": "bad", "bbox_hint": [0, 0, float("nan"), 20]})
    entities = [{"id": "shape", "measurement": {"layout_bbox": {"px": [10, 10, 30, 20]}}}]
    decision = {"entity_id": "shape", "before_bbox_px": [10, 10, 30, 20], "after_bbox_px": [90, 10, 30, 20], "reviewed_by": "host_agent_visual_reasoning", "reason": "Regression probe"}
    with pytest.raises(ValueError, match="outside"):
        normalize_local_geometry(entities, {"geometry_adjustments": [decision]}, {}, (100, 100))
    assert entities[0]["measurement"]["layout_bbox"]["px"] == [10, 10, 30, 20]


def test_measurement_crop_uses_the_selected_geometry_and_safe_filenames(tmp_path):
    pixels = np.full((100, 200, 3), 255, np.uint8)
    pixels[30:60, 50:90] = [20, 100, 180]
    image = tmp_path / "target.png"
    Image.fromarray(pixels).save(image)
    entity = {"id": "../art", "kind": "image", "geometry_policy": "opencv_visible", "bbox_hint": [0, 0, 200, 100], "z": 0}
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps({"entities": [entity]}))
    config = tmp_path / "config.json"
    config.write_text("{}")
    output = tmp_path / "measurement"
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/runtime/scripts/measure_visual_scene.py"), str(image), "--semantic-map", str(semantic), "--config", str(config), "--output-dir", str(output), "--sam", "never"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    record = json.loads((output / "slide_entities.json").read_text())["entities"][0]["measurement"]
    crop = Path(record["image_object"]["screenshot_crop_absolute"])
    assert crop.parent == output / "crops"
    with Image.open(crop) as saved:
        assert list(saved.size) == record["layout_bbox"]["px"][2:]
    assert record["source_crop_bbox"] == record["layout_bbox"]


def test_multislide_native_geometry_and_chart_direction(tmp_path):
    base = {"dimensions_px": [1600, 900], "objects": [
        {"id": "card", "kind": "shape", "shape": "rounded_rectangle", "bbox_px": [80, 80, 360, 200], "round_rect_adjustment": 5000, "style": {"fill": "#E5EDF5", "stroke": "none"}},
        {"id": "islands", "kind": "freeform", "bbox_px": [100, 350, 300, 100], "coordinates": "absolute", "contours_px": [[[100, 350], [200, 350], [200, 450], [100, 450]], [[300, 350], [400, 350], [400, 450], [300, 450]]], "style": {"fill": "#21618C", "stroke": "none"}},
        {"id": "data", "kind": "chart", "bbox_px": [650, 100, 700, 450], "structure": {"type": "bar", "categories": ["One", "Two"], "series": [{"name": "Series", "values": [3, 7]}]}},
    ]}
    second = copy.deepcopy(base)
    second["objects"][0]["round_rect_adjustment"] = 35000
    second["objects"][2]["structure"]["type"] = "column"
    spec = tmp_path / "probe.json"
    spec.write_text(json.dumps({"slides": [base, second]}))
    output = tmp_path / "probe.pptx"
    result = subprocess.run(["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(output)], env={**os.environ, "PYTHON": sys.executable}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        for index, expected in enumerate([5000, 35000], 1):
            slide = ET.fromstring(archive.read(f"ppt/slides/slide{index}.xml"))
            adjustment = slide.find('.//a:prstGeom[@prst="roundRect"]/a:avLst/a:gd', NS)
            assert adjustment.attrib["fmla"] == f"val {expected}"
            assert len(slide.findall(".//a:custGeom/a:pathLst/a:path/a:moveTo", NS)) == 2
            first = slide.find(".//a:custGeom/a:pathLst/a:path/a:moveTo/a:pt", NS)
            assert first.attrib == {"x": "0", "y": "0"}
        for index, direction in enumerate(["bar", "col"], 1):
            chart = ET.fromstring(archive.read(f"ppt/charts/chart{index}.xml"))
            assert chart.find(".//c:barDir", NS).attrib["val"] == direction


def test_deck_history_preserves_page_work_after_the_live_deck_changes(tmp_path):
    (tmp_path / "session.json").write_text("{}")
    (tmp_path / "session-overrides.json").write_text('{"profile":"example"}')
    work = tmp_path / "slides/s1/work"
    work.mkdir(parents=True)
    target = work / "accepted-slide.png"
    target.write_bytes(b"first image")
    version = run_versions.archive(tmp_path)
    archived = Path(version["path"])
    assert (archived / "slides/s1/work/accepted-slide.png").read_bytes() == b"first image"
    target.write_bytes(b"second image")
    (tmp_path / "session-overrides.json").write_text('{"profile":"revised"}')
    assert (archived / "slides/s1/work/accepted-slide.png").read_bytes() == b"first image"
    assert (archived / "session-overrides.json").read_text() == '{"profile":"example"}'


def test_failed_packaging_preserves_previous_archive(tmp_path, monkeypatch):
    skill = tmp_path / "source"
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text("test")
    (skill / "agents/openai.yaml").write_text("test")
    destination = tmp_path / "deliverables"
    destination.mkdir()
    archive = destination / "skill.zip"
    archive.write_bytes(b"previous archive")
    monkeypatch.setattr(package_self, "ROOT", skill)
    monkeypatch.setattr(package_self, "MAX_BYTES", 1)
    monkeypatch.setattr(package_self, "run", lambda *args: None)
    monkeypatch.setattr(sys, "argv", ["package_self.py", "--output-dir", str(destination)])
    with pytest.raises(SystemExit, match="exceeds"):
        package_self.main()
    assert archive.read_bytes() == b"previous archive"
    assert list(destination.iterdir()) == [archive]


def test_node_postprocessor_uses_current_python(monkeypatch):
    monkeypatch.setenv("PYTHON", "unrelated-python")
    assert slidepoise_runtime.node_environment()["PYTHON"] == sys.executable


def test_failed_native_postprocessing_preserves_previous_presentation(tmp_path):
    spec = tmp_path / "scene.json"
    spec.write_text(json.dumps({"dimensions_px": [800, 450], "objects": []}))
    output = tmp_path / "presentation.pptx"
    output.write_bytes(b"previous presentation")
    result = subprocess.run(["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(output)], env={**os.environ, "PYTHON": str(tmp_path / "missing-python")}, capture_output=True, text=True)
    assert result.returncode != 0
    assert output.read_bytes() == b"previous presentation"
    assert not list(tmp_path.glob(".slidepoise-render-*"))


def test_finalized_font_size_and_undirected_connectors_survive_emission(tmp_path):
    scene = json.loads((ROOT / "tests/fixtures/continuous_connector_scene.json").read_text())["slide"]
    # The fixture is a constructor scene, with already resolved route geometry.
    for obj in scene["objects"]:
        if obj["kind"] == "connector_graph":
            obj["arrowhead_treatment"] = "none"
    scene["objects"].append({"id": "precise-text", "kind": "textbox", "text": "Measured type", "bbox_px": [20, 20, 300, 60], "style": {"font_size_pt": 17.25}})
    spec = tmp_path / "scene.json"
    spec.write_text(json.dumps(scene))
    output = tmp_path / "scene.pptx"
    result = subprocess.run(["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(output)], env={**os.environ, "PYTHON": sys.executable}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        assert any(item.attrib.get("sz") == "1725" for item in slide.findall(".//a:rPr", NS))
        assert all(item.attrib.get("type", "none") == "none" for item in slide.findall(".//a:tailEnd", NS) + slide.findall(".//a:headEnd", NS))


def test_failed_json_serialization_cleans_staging_file(tmp_path):
    output = tmp_path / "state.json"
    output.write_text('{"previous":true}')
    with pytest.raises(TypeError):
        storage.write(output, {"value": object()})
    assert output.read_text() == '{"previous":true}'
    assert list(tmp_path.iterdir()) == [output]


def test_profile_style_substitutions_are_reported():
    style = _base_style({"style_hint": {"font_family": "Other", "italic": True, "color": "#FF0000"}}, {
        "style": {"body_font": "Arial"},
        "profile_hard_rules": {"typography": {"italics_allowed": False, "ordinary_text_colors": ["#000000"]}},
    })
    changes = {item["property"]: item for item in style["profile_adjustments"]}
    assert changes["font_family"]["requested"] == "Other"
    assert changes["font_family"]["resolved"] == "Arial"
    assert changes["italic"]["resolved"] is False
    assert changes["color"]["resolved"] == "#000000"


def test_nonfinite_search_bounds_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        _largest_size([], {}, float("inf"), 0.5)


def test_measured_table_margins_scale_with_source_geometry():
    scene = {"source": {"width_px": 800, "height_px": 450}, "entities": [{
        "id": "table", "kind": "table", "reconstruction_route": "native_table", "z": 0,
        "measurement": {"layout_bbox": {"px": [20, 20, 300, 200]}},
        "table_structure": {"rows": [[{"text": "Pixels", "margin_px": [4, 8, 4, 8]},
                                        {"text": "Points", "options": {"margin": 3}}]]}}]}
    design = {"full_slide_px": [1600, 900], "frame": {"header": {"enabled": False}, "footer": {"enabled": False}}}
    contract = build_reconstruction_contract(scene, design)
    result = build_reconstruction_scene(measured_scene=scene, contract=contract, design=design, slide_id="table")
    table = result["objects"][0]
    assert table["bbox_px"] == [40, 40, 600, 400]
    assert table["structure"]["rows"][0][0]["margin_px"] == [8, 16, 8, 16]
    assert table["structure"]["rows"][0][1]["options"]["margin"] == 3
    assert scene["entities"][0]["table_structure"]["rows"][0][0]["margin_px"] == [4, 8, 4, 8]
