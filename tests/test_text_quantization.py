"""Half-point typography survives physical-unit conversion and actual OOXML."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

from test_native_presentation import emit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/runtime/src"))
from slidepoise.reconstruction.contract import build_reconstruction_contract
from slidepoise.reconstruction.scene import build_reconstruction_scene
from slidepoise.reconstruction.text_fit import _floor_step, finalize_fitted_text_entities

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def text_entity(name, size, y=0, height=110):
    return {"id": name, "kind": "text", "text": "Native size", "z": 1,
            "reconstruction_route": "native_text", "typography_group": name, "text_style_role": "body",
            "style_hint": {"font_family": "Arial", "target_font_size_px": size, "line_spacing": 1},
            "measurement": {"layout_bbox": {"px": [40, y, 900, height]}}}


def test_roundoff_near_a_half_point_does_not_change_its_step():
    for points in (14, 16, 24, 32, 34):
        assert _floor_step(points * 0.999999975, 0.5) == points
        assert _floor_step(points - 0.001, 0.5) == points - 0.5


def test_real_overflow_still_reduces_the_authored_target_and_reports_why():
    entity = text_entity("tight", 64, height=30)
    finalized, report = finalize_fitted_text_entities([entity], {}, {}, points_per_px=0.4999999875)
    group = report["text_groups"][0]
    assert finalized["tight"]["font_size_pt"] < 32
    assert group["agent_target_ceiling_pt"] == 32
    assert group["reduced_from_agent_target"] is True
    assert group["reduced_for_fit"] is True
    assert group["members_not_fitting_target"] == ["tight"]


def test_quantization_reduction_is_distinguished_from_failure_to_fit():
    entity = text_entity("fractional", 63.99)
    _, report = finalize_fitted_text_entities([entity], {}, {}, points_per_px=0.5)
    group = report["text_groups"][0]
    assert group["shared_font_size_pt"] == 31.5
    assert group["quantization_reduction_pt"] == pytest.approx(0.495)
    assert group["reduced_from_agent_target"] is True
    assert group["reduced_for_fit"] is False
    assert group["members_not_fitting_target"] == []


def test_compiled_targets_tables_and_master_keep_exact_native_font_sizes(tmp_path):
    targets = (64, 32, 28, 68, 48)
    measured = {"source": {"width_px": 1920, "height_px": 960},
                "entities": [text_entity(f"size-{size}", size, 20 + index * 130) for index, size in enumerate(targets)]}
    design = {"full_slide_px": [1920, 1080], "frame": {
        "header": {"enabled": True, "height_px": 64, "left_text": "Shared title", "font_family": "Arial", "font_size_px": 28},
        "footer": {"enabled": True, "height_px": 56, "left_text": "Shared footer", "font_family": "Arial", "font_size_px": 20,
                   "slide_number": {"enabled": True}}}}
    contract = build_reconstruction_contract(measured, design)
    scene = build_reconstruction_scene(measured_scene=measured, contract=contract, design=design, slide_id="precision")
    groups = scene["compiler_report"]["text_fitting"]["text_groups"]
    assert {group["shared_font_size_pt"] for group in groups} == {size / 2 for size in targets}
    assert all(not group["reduced_from_agent_target"] for group in groups)
    scene["objects"].append({"id": "table", "kind": "table", "bbox_px": [40, 760, 1300, 110],
                             "structure": {"rows": [["A table uses the same point conversion"]]},
                             "style": {"font_family": "Arial", "font_size_px": 28 * 0.999999975}})
    result, output = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        for shape in slide.findall(".//p:sp", NS):
            name = shape.find("p:nvSpPr/p:cNvPr", NS).get("name")
            if name.startswith("size-"):
                size = int(name.removeprefix("size-"))
                assert {int(prop.get("sz")) for prop in shape.findall(".//a:rPr", NS)} == {size * 50}
        assert {int(prop.get("sz")) for prop in slide.findall(".//a:tbl//a:rPr", NS)} == {1400}
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        assert presentation.find("p:sldSz", NS).get("cx") == "12192000"
        inherited = [ET.fromstring(archive.read(name)) for name in archive.namelist()
                     if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml")]
        text_sizes = {}
        for root in inherited:
            for run in root.findall(".//a:r", NS):
                text = run.find("a:t", NS)
                props = run.find("a:rPr", NS)
                if text is not None and props is not None:
                    text_sizes[text.text] = int(props.get("sz"))
        assert text_sizes["Shared title"] == 1400
        assert text_sizes["Shared footer"] == 1000
    (tmp_path / "typography-report.json").write_text(json.dumps(groups, indent=2))
