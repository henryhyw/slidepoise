"""Native PowerPoint properties that real showcase reconstruction depends on."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/runtime/src"))

from slidepoise.reconstruction.text_fit import fit_text_entities, finalize_fitted_text_entities

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}


def emit(scene, directory):
    source = directory / "scene.json"
    source.write_text(json.dumps(scene))
    target = directory / "slide.pptx"
    result = subprocess.run(["node", str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(source), "--output", str(target)],
                            env={**os.environ, "PYTHON": sys.executable}, text=True, capture_output=True)
    return result, target


def test_editorial_type_open_arrows_and_chart_presentation_survive_native_output(tmp_path):
    scene = {"dimensions_px": [1600, 900], "objects": [
        {"id": "tracked-title", "kind": "textbox", "text": "A point of view", "bbox_px": [50, 50, 1000, 100], "style": {"font_size_pt": 48, "char_spacing_px": -3, "line_spacing_multiple": 1.25}},
        {"id": "flow", "kind": "connector_graph", "source_routes_px": [], "target_routes_px": [[[50, 200], [400, 200]]], "arrowhead_treatment": "open_arrow_at_target", "style": {"width_px": 1}},
        {"id": "baseline", "kind": "chart", "bbox_px": [50, 300, 1000, 500], "structure": {"type": "bar", "categories": ["Research", "Drafting"], "series": [{"name": "Hours", "values": [12, 8]}], "show_legend": False, "show_category_axis": False, "show_value_axis": False, "category_order": "reverse", "value_axis_maximum": 12, "gap_width_pct": 50, "plot_layout": {"x": 0, "y": 0, "w": 1, "h": 1}}},
    ]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        assert slide.find('.//a:rPr[@spc="-180"]', NS) is not None
        assert slide.find('.//a:lnSpc/a:spcPct[@val="125000"]', NS) is not None
        assert slide.find('.//a:tailEnd[@type="arrow"]', NS) is not None
        chart = ET.fromstring(archive.read("ppt/charts/chart1.xml"))
        assert chart.find(".//c:gapWidth", NS).get("val") == "50"
        assert chart.find(".//c:catAx/c:scaling/c:orientation", NS).get("val") == "maxMin"
        assert chart.find(".//c:valAx/c:scaling/c:max", NS).get("val") == "12"
        assert chart.find(".//c:catAx/c:delete", NS).get("val") == "1"
        assert chart.find(".//c:valAx/c:delete", NS).get("val") == "1"
        assert chart.find(".//c:manualLayout/c:w", NS).get("val") == "1"


def test_malformed_chart_data_cannot_overwrite_a_usable_deck(tmp_path):
    target = tmp_path / "slide.pptx"
    target.write_bytes(b"previous usable output")
    result, _ = emit({"dimensions_px": [1600, 900], "objects": [{"id": "bad-chart", "kind": "chart", "bbox_px": [50, 50, 500, 400], "structure": {"categories": ["One"], "series": [{"values": [1, 2]}]}}]}, tmp_path)
    assert result.returncode != 0
    assert "matching category labels" in result.stderr
    assert target.read_bytes() == b"previous usable output"


@pytest.mark.parametrize(("chart_type", "bar_direction"), [("column", "col"), ("bar", "bar")])
def test_chart_type_preserves_authored_orientation(tmp_path, chart_type, bar_direction):
    scene = {"dimensions_px": [1600, 900], "objects": [{
        "id": "capacity", "kind": "chart", "bbox_px": [50, 50, 600, 400],
        "structure": {"type": chart_type, "categories": ["Research", "Drafting"],
                      "series": [{"name": "Hours", "values": [12, 8]}]},
    }]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        chart = ET.fromstring(archive.read("ppt/charts/chart1.xml"))
        assert chart.find(".//c:barDir", NS).get("val") == bar_direction


def test_native_table_preserves_word_level_formatting_with_component_styling(tmp_path):
    scene = {"dimensions_px": [1600, 900], "objects": [{
        "id": "workstreams", "kind": "table", "bbox_px": [40, 40, 900, 250],
        "style": {"font_size_pt": 18, "font_family": "Arial", "vertical_alignment": "middle"},
        "structure": {"table_style": {"header_row_fill": "#000000", "header_bold": True},
                      "rows": [[{"text": "Workstream", "options": {"color": "FFFFFF"}}],
                               [{"text": [{"text": "Data & access", "options": {"bold": True}},
                                          {"text": "\nSource steward", "options": {"bold": False}}]}]]},
    }]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        root = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        cells = root.findall(".//a:tbl/a:tr/a:tc", NS)
        assert len(cells) == 2
        assert all(cell.find("a:tcPr", NS).get("anchor") == "ctr" for cell in cells)
        runs = cells[1].findall(".//a:r", NS)
        assert [(run.find("a:t", NS).text, run.find("a:rPr", NS).get("b", "0")) for run in runs] == [
            ("Data & access", "1"), ("Source steward", "0")]


def test_invalid_table_runs_cannot_replace_a_usable_deck(tmp_path):
    target = tmp_path / "slide.pptx"
    target.write_bytes(b"previous usable output")
    scene = {"dimensions_px": [1600, 900], "objects": [{"id": "table", "kind": "table", "bbox_px": [40, 40, 900, 250],
             "structure": {"rows": [[{"text": [{"text": {"unexpected": "object"}}]}]]}}]}
    result, _ = emit(scene, tmp_path)
    assert result.returncode != 0 and "Table rich text" in result.stderr
    assert target.read_bytes() == b"previous usable output"


@pytest.mark.parametrize("value", [None, True, "", "12"])
def test_chart_values_are_never_silently_coerced_into_numbers(tmp_path, value):
    target = tmp_path / "slide.pptx"
    target.write_bytes(b"previous usable output")
    scene = {"dimensions_px": [1600, 900], "objects": [{"id": "reported-hours", "kind": "chart", "bbox_px": [50, 50, 500, 400],
             "structure": {"categories": ["Research"], "series": [{"name": "Hours", "values": [value]}]}}]}
    result, _ = emit(scene, tmp_path)
    assert result.returncode != 0 and "finite numeric values" in result.stderr
    assert target.read_bytes() == b"previous usable output"


def test_chart_retains_zero_and_negative_fractional_values(tmp_path):
    scene = {"dimensions_px": [1600, 900], "objects": [{"id": "change", "kind": "chart", "bbox_px": [50, 50, 500, 400],
             "structure": {"categories": ["Baseline", "Change"], "series": [{"name": "Hours", "values": [0, -2.75]}]}}]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        chart = ET.fromstring(archive.read("ppt/charts/chart1.xml"))
        values = chart.findall(".//c:val/c:numRef/c:numCache/c:pt/c:v", NS)
        assert [float(value.text) for value in values] == [0, -2.75]


def test_chart_values_are_workbook_bound_native_labels_with_authored_typography(tmp_path):
    scene = {"dimensions_px": [1600, 900], "objects": [{"id": "hours", "kind": "chart", "bbox_px": [50, 50, 600, 400],
             "structure": {"categories": ["Research", "Drafting"], "series": [{"name": "Hours", "values": [12, 8]}],
                           "show_values": True, "data_label_position": "outEnd", "data_label_format_code": "0",
                           "data_font_family": "Arial", "data_font_size_px": 27.5, "data_label_color": "#123456",
                           "data_label_colors": ["#FD5108", "#000000"]}}]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        chart = ET.fromstring(archive.read("ppt/charts/chart1.xml"))
        labels = chart.find(".//c:dLbls", NS)
        assert labels.find("c:showVal", NS).get("val") == "1"
        assert labels.find("c:dLblPos", NS).get("val") == "outEnd"
        assert labels.find("c:numFmt", NS).get("formatCode") == "0"
        formatting = labels.find("c:txPr/a:p/a:pPr/a:defRPr", NS)
        assert formatting.get("sz") == "1650"
        assert formatting.find("a:latin", NS).get("typeface") == "Arial"
        assert formatting.find("a:solidFill/a:srgbClr", NS).get("val") == "123456"
        points = labels.findall("c:dLbl", NS)
        assert [(item.find("c:idx", NS).get("val"), item.find(".//a:srgbClr", NS).get("val")) for item in points] == [("0", "FD5108"), ("1", "000000")]
        for point in points:
            assert point.find("c:showVal", NS).get("val") == "1"
            for flag in ("showLegendKey", "showCatName", "showSerName", "showPercent", "showBubbleSize"):
                assert point.find(f"c:{flag}", NS).get("val") == "0"
            assert point.find("c:numFmt", NS).get("formatCode") == "0"
        assert chart.find(".//c:externalData", NS) is not None
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        assert slide.findall(".//a:t", NS) == []


@pytest.mark.parametrize("options", [{"gap_width_pct": "50"}, {"value_axis_maximum": None},
                                     {"value_axis_minimum": 5, "value_axis_maximum": 2},
                                     {"data_font_size_px": 0}, {"data_font_size_px": True},
                                     {"data_label_colors": []}, {"data_label_colors": ["orange"]},
                                     {"data_label_position": "outer-ish"}])
def test_invalid_numeric_chart_options_do_not_fall_back_silently(tmp_path, options):
    target = tmp_path / "slide.pptx"
    target.write_bytes(b"previous usable output")
    scene = {"dimensions_px": [1600, 900], "objects": [{"id": "bounded-values", "kind": "chart", "bbox_px": [50, 50, 500, 400],
             "structure": {"categories": ["Research"], "series": [{"values": [3]}], **options}}]}
    result, _ = emit(scene, tmp_path)
    assert result.returncode != 0 and "Chart bounded-values" in result.stderr
    assert target.read_bytes() == b"previous usable output"


def fitting_entity(spacing):
    return {"id": "scope", "kind": "text", "text": "One workflow\nOne owner", "text_style_role": "body", "typography_group": "scope",
            "measurement": {"layout_bbox": {"px": [50, 50, 400, 100]}},
            "style_hint": {"target_font_size_px": 20, "line_spacing": spacing}}


def test_authored_line_spacing_survives_fitting_and_finalization():
    entity = fitting_entity(1.25)
    fitted, _ = fit_text_entities([entity], {})
    finalized, _ = finalize_fitted_text_entities([entity], {}, fitted, points_per_px=0.6)
    assert fitted["scope"]["line_spacing"] == finalized["scope"]["line_spacing"] == 1.25
    assert finalized["scope"]["authored_text"] == entity["text"]
    fitted["scope"]["line_spacing"] = float("nan")
    with pytest.raises(ValueError, match="scope line_spacing"):
        finalize_fitted_text_entities([entity], {}, fitted, points_per_px=0.6)


@pytest.mark.parametrize("spacing", [0, -0.5, True, None, "1.2"])
def test_invalid_line_spacing_is_rejected_by_fitting_and_native_emission(tmp_path, spacing):
    with pytest.raises(ValueError, match="scope line_spacing"):
        fit_text_entities([fitting_entity(spacing)], {})
    target = tmp_path / "slide.pptx"
    target.write_bytes(b"previous usable output")
    result, _ = emit({"dimensions_px": [1600, 900], "objects": [
        {"id": "scope", "kind": "textbox", "text": "One workflow\nOne owner", "bbox_px": [50, 50, 400, 100],
         "style": {"font_size_pt": 20, "line_spacing_multiple": spacing}}]}, tmp_path)
    assert result.returncode != 0 and "line_spacing_multiple" in result.stderr
    assert target.read_bytes() == b"previous usable output"
