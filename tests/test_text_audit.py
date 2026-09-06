"""Text audits distinguish native table layout from textbox requirements."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pytest

from test_native_presentation import emit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
from audit_powerpoint_text import NS, audit


@pytest.fixture
def native_deck(tmp_path):
    scene = {"dimensions_px": [1600, 900], "objects": [
        {"id": "title", "kind": "textbox", "text": "Accountable release",
         "bbox_px": [50, 50, 1000, 100], "style": {"font_family": "Arial", "font_size_pt": 32}},
        {"id": "owners", "kind": "table", "bbox_px": [50, 200, 1000, 300],
         "style": {"font_family": "Arial", "font_size_pt": 18, "vertical_alignment": "middle"},
         "structure": {"rows": [["Owner", "Control"], ["Expert", "Verify claims"]]}}]}
    result, target = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    return target


def mutate(source, change):
    target = source.with_name("changed.pptx")
    with ZipFile(source) as original, ZipFile(target, "w") as changed:
        for info in original.infolist():
            data = original.read(info)
            if info.filename == "ppt/slides/slide1.xml":
                root = ET.fromstring(data)
                change(root)
                data = ET.tostring(root)
            changed.writestr(info, data)
    return audit(target)


def test_native_tables_use_cell_properties_and_legal_paragraph_defaults(native_deck):
    result = audit(native_deck)
    assert result["finding_count"] == 0, result["findings"]
    cells = [record for record in result["text_bodies"] if record["kind"] == "table_cell"]
    assert len(cells) == 4
    assert all(record["cell_properties"]["anchor"] == "ctr" for record in cells)
    assert all("lIns" not in record["body_properties"] for record in cells)
    assert any(not record["explicit_line_spacing"] for record in cells)
    assert any(not record["explicit_paragraph_alignment"] for record in cells)


@pytest.mark.parametrize("key,value", [("anchor", "mid"), ("marL", "NaN"), ("marT", "2147483648")])
def test_invalid_cell_geometry_is_reported(native_deck, key, value):
    result = mutate(native_deck, lambda root: root.find(".//a:tcPr", NS).set(key, value))
    assert result["findings"] == [{"name": "owners.R1C1", "issue": "invalid cell properties", "values": {key: value}}]


def test_missing_cell_margin_does_not_fall_back_to_textbox_insets(native_deck):
    def change(root):
        root.find(".//a:tcPr", NS).attrib.pop("marL")
        root.find(".//a:tc/a:txBody/a:bodyPr", NS).set("lIns", "0")
    result = mutate(native_deck, change)
    assert result["findings"] == [{"name": "owners.R1C1", "issue": "missing cell properties", "values": ["marL"]}]


def test_textbox_explicit_layout_is_still_checked(native_deck):
    result = mutate(native_deck, lambda root: root.find(".//p:sp/p:txBody/a:bodyPr", NS).attrib.pop("wrap"))
    assert result["findings"] == [{"name": "title", "issue": "missing body properties", "values": ["wrap"]}]


@pytest.mark.parametrize("defect,issue", [("font", "all_runs_have_font"), ("size", "all_runs_have_size"),
                                         ("invalid_size", "invalid font sizes"), ("autofit", "autofit is implicit")])
def test_native_cells_retain_real_text_checks(native_deck, defect, issue):
    def change(root):
        body = root.find(".//a:tc/a:txBody", NS)
        run_properties = body.find(".//a:rPr", NS)
        if defect == "font":
            run_properties.remove(run_properties.find("a:latin", NS))
        elif defect == "size":
            run_properties.attrib.pop("sz")
        elif defect == "invalid_size":
            run_properties.set("sz", "NaN")
        else:
            properties = body.find("a:bodyPr", NS)
            properties.remove(properties.find("a:noAutofit", NS))
    result = mutate(native_deck, change)
    assert result["finding_count"] == 1
    assert result["findings"][0]["name"] == "owners.R1C1"
    assert result["findings"][0]["issue"] == issue
