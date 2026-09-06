"""Authored route direction and geometry must survive the actual Office reader."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image

from test_preview_rendering import require_preview_tools, run


ROOT = Path(__file__).resolve().parents[1]
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def test_reverse_lines_and_return_paths_survive_actual_office_rendering(tmp_path):
    tools = require_preview_tools()
    paths = {
        "forward": [[100, 100], [400, 100]],
        "reverse": [[400, 200], [100, 200]],
        "return": [[800, 330], [800, 460], [500, 460], [500, 330]],
        "elbow": [[900, 600], [1100, 600], [1100, 780]],
    }
    source = tmp_path / "routes.json"
    source.write_text(json.dumps({"dimensions_px": [1600, 900], "background": "#FFFFFF", "objects": [
        {"id": name, "kind": "connector_graph", "source_routes_px": [], "target_routes_px": [points],
         "arrowhead_treatment": "triangle_at_target", "style": {"color": "#000000", "width_px": 4}}
        for name, points in paths.items()
    ]}), encoding="utf-8")
    powerpoint = tmp_path / "routes.pptx"
    run(tools["Node"], str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"),
        "--input", str(source), "--output", str(powerpoint))
    with zipfile.ZipFile(powerpoint) as archive:
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
    connectors = slide.findall(".//p:cxnSp", NS)
    assert len(connectors) == 2
    for connector in connectors:
        assert connector.find("p:spPr/a:prstGeom", NS).get("prst") == "line"
        assert connector.find("p:spPr/a:custGeom", NS) is None
    reverse = next(shape for shape in connectors if "reverse" in shape.find("p:nvCxnSpPr/p:cNvPr", NS).get("name"))
    assert reverse.find("p:spPr/a:xfrm", NS).get("flipH") == "1"
    freeforms = [shape for shape in slide.findall(".//p:sp", NS)
                 if shape.find("p:nvSpPr/p:cNvPr", NS).get("name", "").startswith("SC_FREEFORM_ROUTE__")]
    assert len(freeforms) == 2
    returning = next(shape for shape in freeforms if "return" in shape.find("p:nvSpPr/p:cNvPr", NS).get("name"))
    points = returning.findall(".//a:path/*/a:pt", NS)
    assert len(points) == 4
    assert points[0].get("x") == points[1].get("x")
    assert points[2].get("x") == points[3].get("x") == "0"
    assert points[0].get("y") == points[3].get("y") == "0"
    assert returning.find(".//a:tailEnd", NS).attrib == {"type": "triangle", "w": "lg", "len": "lg"}

    # The previous custom-geometry connector XML looked correct, but Office
    # rendered a different route. Pixel checks exercise that reader boundary.
    preview = tmp_path / "routes.png"
    run(sys.executable, str(ROOT / "slidepoise/scripts/slidepoise_runtime.py"),
        "render-preview", "--pptx", str(powerpoint), "--output", str(preview), "--dpi", "96")
    with Image.open(preview) as image:
        rgb = image.convert("RGB")

        def ink_near(x, y):
            px, py = round(x * rgb.width / 1600), round(y * rgb.height / 900)
            crop = rgb.crop((px - 2, py - 2, px + 3, py + 3))
            return any(max(crop.getpixel((x, y))) < 150 for x in range(crop.width) for y in range(crop.height))

        for point in [(250, 100), (250, 200), (800, 395), (650, 460), (500, 395), (1000, 600), (1100, 700)]:
            assert ink_near(*point), f"Office lost an authored route segment near {point}"
        assert not ink_near(650, 395), "Office invented a central bend in the return route"
        assert ink_near(110, 205) and not ink_near(90, 205), "Reverse arrow points away from its authored target"
        assert ink_near(505, 340) and not ink_near(505, 320), "Return arrow no longer points upward"
