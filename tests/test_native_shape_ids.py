"""Mixed native objects have unique drawing IDs without corrupting references."""
import copy
import json
from pathlib import Path
import sys
import zipfile

from lxml import etree
from PIL import Image, ImageChops
import pytest

from test_preview_rendering import require_preview_tools, run

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
import postprocess_pptx as native


def referenced_collision_xml(reference_id="17", reference_kind="connector"):
    reference = (f'<a:stCxn id="{reference_id}" idx="2"/><a:endCxn id="23" idx="0"/>'
                 if reference_kind == "connector" else "")
    timing = f'<p:timing><p:spTgt spid="{reference_id}"/></p:timing>' if reference_kind == "timing" else ""
    return f'''<p:sld xmlns:p="{native.NS['p']}" xmlns:a="{native.NS['a']}"><p:cSld><p:spTree>
      <p:sp><p:nvSpPr><p:cNvPr id="17" name="source"/></p:nvSpPr><p:spPr/></p:sp>
      <p:sp><p:nvSpPr><p:cNvPr id="23" name="target"/></p:nvSpPr><p:spPr/></p:sp>
      <p:sp><p:nvSpPr><p:cNvPr id="2" name="first"/></p:nvSpPr><p:spPr/></p:sp>
      <p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="2" name="table"/></p:nvGraphicFramePr></p:graphicFrame>
      <p:cxnSp><p:nvCxnSpPr><p:cNvPr id="32" name="attached"/><p:cNvCxnSpPr>{reference}</p:cNvCxnSpPr></p:nvCxnSpPr>
      <p:spPr><a:xfrm><a:off x="100" y="200"/><a:ext cx="300" cy="400"/></a:xfrm></p:spPr></p:cxnSp>
      </p:spTree></p:cSld>{timing}</p:sld>'''


def test_collision_repair_preserves_unambiguous_connection_and_timing_targets():
    for kind in ("connector", "timing"):
        root = native.parse_xml(referenced_collision_xml(reference_kind=kind))
        original = copy.deepcopy(root)
        assert native.normalize_shape_ids(root) == 1
        properties = root.findall(".//p:cNvPr", native.NS)
        ids = [item.get("id") for item in properties]
        assert len(set(ids)) == len(ids)
        assert {item.get("name"): item.get("id") for item in properties if item.get("name") != "table"} == {
            "source": "17", "target": "23", "first": "2", "attached": "32"}
        for xpath in (".//a:stCxn", ".//a:endCxn", ".//p:spTgt", ".//a:xfrm"):
            assert [etree.tostring(item) for item in root.findall(xpath, native.NS)] == [
                etree.tostring(item) for item in original.findall(xpath, native.NS)]
        assert native.normalize_shape_ids(root) == 0


@pytest.mark.parametrize("kind", ["connector", "timing"])
def test_ambiguous_reference_never_overwrites_the_original_archive(tmp_path, kind):
    target = tmp_path / "ambiguous.pptx"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", referenced_collision_xml("2", kind))
    before = target.read_bytes()
    with pytest.raises(ValueError, match="Ambiguous native drawing reference 2"):
        native.postprocess(target)
    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]


def test_layouts_and_masters_have_the_same_local_uniqueness_boundary(tmp_path):
    target = tmp_path / "inherited.pptx"
    with zipfile.ZipFile(target, "w") as archive:
        for part in ("slides/slide1", "slideLayouts/slideLayout1", "slideMasters/slideMaster1"):
            archive.writestr(f"ppt/{part}.xml", referenced_collision_xml())
    assert native.postprocess(target)["shapeIdsNormalized"] == 3
    assert native.postprocess(target)["shapeIdsNormalized"] == 0


def test_mixed_shapes_tables_charts_and_connectors_have_unique_ids_in_actual_office(tmp_path):
    tools = require_preview_tools()
    objects = [
        {"id": "title", "kind": "textbox", "text": "Native objects remain editable", "bbox_px": [40, 25, 1100, 65], "style": {"font_family": "Arial", "font_size_pt": 30}},
        {"id": "divider", "kind": "shape", "shape": "rectangle", "bbox_px": [580, 120, 2, 410], "style": {"fill": "#222222"}},
        {"id": "assumptions", "kind": "table", "bbox_px": [40, 140, 480, 150], "style": {"font_family": "Arial", "font_size_pt": 18}, "structure": {"rows": [["Research", "12 hours"], ["Review", "8 hours"]]}},
        {"id": "hours", "kind": "chart", "bbox_px": [650, 140, 480, 350], "structure": {"type": "bar", "categories": ["Research", "Review"], "series": [{"name": "Hours", "values": [12, 8]}], "show_values": True, "show_legend": False}},
        {"id": "support-rule", "kind": "shape", "shape": "rectangle", "bbox_px": [40, 340, 480, 2], "style": {"fill": "#222222"}},
        {"id": "gate", "kind": "table", "bbox_px": [40, 380, 480, 100], "style": {"font_family": "Arial", "font_size_pt": 18}, "structure": {"rows": [["Scale gate", "Expert signoff"]]}},
        {"id": "flow", "kind": "connector_graph", "source_routes_px": [], "target_routes_px": [[[520, 570], [700, 570]]], "arrowhead_treatment": "triangle_at_target", "style": {"color": "#FD5108", "width_px": 4}},
    ]
    source = tmp_path / "mixed.json"
    source.write_text(json.dumps({"slides": [{"slide_id": f"page-{index}", "dimensions_px": [1200, 675], "objects": objects} for index in (1, 2)]}))
    target = tmp_path / "mixed.pptx"
    run(tools["Node"], str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(source), "--output", str(target))
    with zipfile.ZipFile(target) as archive:
        for index in (1, 2):
            slide = native.parse_xml(archive.read(f"ppt/slides/slide{index}.xml").decode())
            properties = slide.findall(".//p:cNvPr", native.NS)
            ids = [item.get("id") for item in properties]
            assert len(set(ids)) == len(ids)
            assert {"assumptions", "hours", "gate", "divider", "support-rule"}.issubset({item.get("name") for item in properties})
            assert len(slide.findall(".//a:tbl", native.NS)) == 2
            assert len(slide.findall(".//c:chart", native.NS)) == 1
            assert len(slide.findall(".//p:cxnSp", native.NS)) == 1
        # Workbook and chart relationships survive shape-identity repair.
        assert len([name for name in archive.namelist() if name.endswith(".xlsx")]) == 2
    preview = tmp_path / "preview"
    run(sys.executable, str(ROOT / "slidepoise/scripts/slidepoise_runtime.py"), "render-deck-preview", "--pptx", str(target), "--output-dir", str(preview), "--dpi", "96")
    pages = run(tools["pdftotext"], "-layout", str(preview / "presentation.pdf"), "-").split("\f")
    for page in pages[:2]:
        assert "Native objects remain editable" in page
        assert "12 hours" in page and "8 hours" in page and "Expert signoff" in page
    with Image.open(preview / "slide-001.png") as first, Image.open(preview / "slide-002.png") as second:
        assert ImageChops.difference(first.convert("RGB"), second.convert("RGB")).getbbox() is None
