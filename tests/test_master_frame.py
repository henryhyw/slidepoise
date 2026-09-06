"""Repeated frames share an actual native master and survive Office rendering."""
import copy
import json
from pathlib import Path
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from test_preview_rendering import require_preview_tools, run

ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/package/2006/relationships"}


def related_part(archive, source, suffix):
    parent, name = posixpath.split(source)
    relationships = ET.fromstring(archive.read(f"{parent}/_rels/{name}.rels"))
    relation = next(item for item in relationships if item.get("Type").endswith(suffix))
    return posixpath.normpath(posixpath.join(parent, relation.get("Target")))


def test_identical_frame_reuses_master_with_live_page_numbers(tmp_path):
    tools = require_preview_tools()
    frame = {"header": {"enabled": True, "height_px": 64, "left_text": "SHARED HEADER", "right_text": "REVIEW COPY",
                         "font_family": "Arial", "font_size_px": 24, "font_weight": "bold", "outer_padding_px": 40},
             "footer": {"enabled": True, "height_px": 56, "left_text": "SHARED FOOTER", "center_text": "",
                         "font_family": "Arial", "font_size_px": 20, "outer_padding_px": 40, "slide_number": {"enabled": True}}}
    slides = []
    labels = ("ALPHA", "BETA", "GAMMA", "DELTA")
    for index, label in enumerate(labels, 1):
        authored = copy.deepcopy(frame)
        authored["slide_number"] = 90 + index
        if index == 2:
            authored["header"] = dict(reversed(list(authored["header"].items())))
        if index == 3:
            authored["header"]["left_text"] = "VARIANT HEADER"
        if index == 4:
            # Missing enabled defaults to true in the shared canvas resolver.
            del authored["header"]["enabled"]
            del authored["footer"]["enabled"]
        slides.append({"slide_id": label.lower(), "dimensions_px": [1200, 720], "frame": authored, "background": "#FFFFFF",
                       "objects": [{"id": "content", "kind": "textbox", "text": f"CONTENT {label}",
                                    "bbox_px": [40, 160, 1100, 100], "style": {"font_family": "Arial", "font_size_pt": 32}}]})
    source = tmp_path / "shared-frame.json"
    source.write_text(json.dumps({"slides": slides}))
    powerpoint = tmp_path / "shared-frame.pptx"
    run(tools["Node"], str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(source), "--output", str(powerpoint))
    with ZipFile(powerpoint) as archive:
        layouts = []
        masters = []
        for index in range(1, len(labels) + 1):
            slide = f"ppt/slides/slide{index}.xml"
            layout = related_part(archive, slide, "/slideLayout")
            layouts.append(layout)
            masters.append(related_part(archive, layout, "/slideMaster"))
            assert b"SHARED HEADER" not in archive.read(slide)
            assert b"SHARED FOOTER" not in archive.read(slide)
        assert masters[0] == masters[1]
        assert layouts[0] == layouts[1]
        assert layouts[2] != layouts[0]
        # PptxGenJS names these masters in its API and serializes their content
        # as inherited slide layouts beneath the presentation's base master.
        shared = ET.fromstring(archive.read(layouts[0]))
        assert shared.find('.//a:fld[@type="slidenum"]', NS) is not None
        assert b'anchor="mid"' not in archive.read(layouts[0])
    preview = tmp_path / "preview"
    run(sys.executable, str(ROOT / "slidepoise/scripts/slidepoise_runtime.py"), "render-deck-preview", "--pptx", str(powerpoint),
        "--output-dir", str(preview), "--dpi", "96")
    pages = run(tools["pdftotext"], "-layout", str(preview / "presentation.pdf"), "-").split("\f")
    for index, label in enumerate(labels, 1):
        text = pages[index - 1]
        assert f"CONTENT {label}" in text
        assert ("VARIANT HEADER" if index == 3 else "SHARED HEADER") in text
        assert "SHARED FOOTER" in text
        assert re.search(rf"SHARED FOOTER[^\n]*\b{index}\s*$", text)
