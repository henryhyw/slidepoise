"""Authored filled paths preserve an explicit absence of an outline in Office."""
import xml.etree.ElementTree as ET
import zipfile

from test_native_presentation import emit


def test_authored_path_preserves_none_and_visible_stroke(tmp_path):
    def polygon(identifier, x, stroke):
        return {"id": identifier, "kind": "freeform", "bbox_px": [x, 40, 120, 80],
                "path_commands_px": [{"op": "M", "point": [x, 40]}, {"op": "L", "point": [x+120, 40]},
                                     {"op": "L", "point": [x+120, 120]}, {"op": "Z"}],
                "style": {"fill": "#FFF5ED", "stroke": stroke, "stroke_width_px": 2}}
    result, target = emit({"dimensions_px": [400, 225], "objects": [
        polygon("fill-only", 20, "none"), polygon("outlined", 180, "#FD5108")
    ]}, tmp_path)
    assert result.returncode == 0, result.stderr
    ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
          "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with zipfile.ZipFile(target) as archive:
        root = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
    shapes = {shape.find("p:nvSpPr/p:cNvPr", ns).get("name"): shape for shape in root.findall(".//p:sp", ns)}
    fill_only_line = shapes["fill-only"].find("p:spPr/a:ln", ns)
    transparent = fill_only_line.find("a:solidFill/a:srgbClr/a:alpha", ns)
    assert fill_only_line.find("a:noFill", ns) is not None or transparent is not None and transparent.get("val") == "0"
    assert shapes["fill-only"].find("p:spPr/a:solidFill/a:srgbClr", ns).get("val") == "FFF5ED"
    visible = shapes["outlined"].find("p:spPr/a:ln/a:solidFill/a:srgbClr", ns)
    assert visible.get("val") == "FD5108"
    assert visible.find("a:alpha", ns) is None or visible.find("a:alpha", ns).get("val") == "100000"
