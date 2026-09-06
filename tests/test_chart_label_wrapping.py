"""Workbook-bound numeric labels retain their authored line policy in Office."""
import importlib.util
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

from test_native_presentation import emit
from test_preview_rendering import require_preview_tools, run


ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
SPEC = importlib.util.spec_from_file_location("chart_wrap_postprocessor", ROOT / "slidepoise/runtime/scripts/postprocess_pptx.py")
POSTPROCESSOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POSTPROCESSOR)


def numeric_chart(**options):
    return {"dimensions_px": [1920, 1080], "objects": [{
        "id": "capacity", "kind": "chart", "bbox_px": [40, 180, 620, 234],
        "structure": {"type": "bar", "categories": ["Discovery", "Drafting", "Review"],
                      "series": [{"name": "Capacity", "values": [2456, 1780, 1230]}],
                      "show_values": True, "show_legend": False, "show_value_axis": False,
                      "show_value_gridlines": False, "category_order": "reverse",
                      "value_axis_maximum": 2456, "gap_width_pct": 50,
                      "plot_layout": {"x": 130 / 620, "y": 0, "w": 353 / 620, "h": 1},
                      "data_label_position": "outEnd", "data_label_format_code": '#,##0" h"',
                      "data_font_family": "Arial", "data_font_size_px": 36, **options},
    }]}


def test_wrap_policy_inherits_into_colored_points_and_preserves_native_references(tmp_path):
    result, target = emit(numeric_chart(data_label_wrap=False, data_label_colors=["#FD5108", "#222222", "#777777"]), tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(target) as archive:
        original = archive.read("ppt/charts/chart1.xml").decode()
        chart = ET.fromstring(original)
        bodies = chart.findall(".//c:dLbls//c:txPr/a:bodyPr", NS)
        assert len(bodies) == 8  # Series and chart group, each with three point treatments.
        assert all(body.get("wrap") == "none" for body in bodies)
        assert chart.find(".//c:externalData", NS) is not None
        assert chart.find(".//c:val/c:numRef/c:f", NS).text.endswith("$B$2:$B$4")
        assert len([name for name in archive.namelist() if name.endswith(".xlsx")]) == 1
        assert ET.fromstring(archive.read("ppt/slides/slide1.xml")).findall(".//a:t", NS) == []
    changed, count = POSTPROCESSOR.transform_chart_labels(original, {"wrap": True})
    assert count == 1
    updated = ET.fromstring(changed)
    assert all(body.get("wrap") == "square" for body in updated.findall(".//c:dLbls//c:txPr/a:bodyPr", NS))
    for node in (".//c:ser", ".//c:externalData"):
        before_node, after_node = chart.find(node, NS), updated.find(node, NS)
        if node.endswith("ser"):
            before_node.remove(before_node.find("c:dLbls", NS))
            after_node.remove(after_node.find("c:dLbls", NS))
        assert ET.tostring(before_node) == ET.tostring(after_node)
    assert POSTPROCESSOR.transform_chart_labels(changed, {"wrap": True})[1] == 0


def test_omitted_policy_keeps_reader_default_and_invalid_policy_preserves_output(tmp_path):
    result, target = emit(numeric_chart(), tmp_path)
    assert result.returncode == 0, result.stderr
    previous = target.read_bytes()
    with zipfile.ZipFile(target) as archive:
        chart = ET.fromstring(archive.read("ppt/charts/chart1.xml"))
    assert all(body.get("wrap") is None for body in chart.findall(".//c:dLbls/c:txPr/a:bodyPr", NS))
    result, _ = emit(numeric_chart(data_label_wrap="false"), tmp_path)
    assert result.returncode != 0 and "data_label_wrap must be a boolean" in result.stderr
    assert target.read_bytes() == previous
    with pytest.raises(ValueError, match="wrap must be a boolean"):
        POSTPROCESSOR.transform_chart_labels(ET.tostring(chart, encoding="unicode"), {"wrap": None})


def test_numeric_labels_stay_on_one_line_in_actual_office_pdf(tmp_path):
    tools = require_preview_tools()
    result, target = emit(numeric_chart(data_label_wrap=False), tmp_path)
    assert result.returncode == 0, result.stderr
    preview = tmp_path / "preview"
    run(sys.executable, str(ROOT / "slidepoise/scripts/slidepoise_runtime.py"),
        "render-deck-preview", "--pptx", str(target), "--output-dir", str(preview), "--dpi", "96")
    lines = run(tools["pdftotext"], "-layout", str(preview / "presentation.pdf"), "-").splitlines()
    for value in ("2,456", "1,780", "1,230"):
        assert any(re.search(re.escape(value) + r"\s+h\b", line) for line in lines), lines
