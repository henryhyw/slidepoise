"""Real Office-to-PDF coverage, separate from compiler and contract unit tests."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "slidepoise/scripts/slidepoise_runtime.py"


def require_preview_tools():
    required = {
        "LibreOffice": shutil.which("libreoffice") or shutil.which("soffice"),
        "pdftoppm": shutil.which("pdftoppm"),
        "pdftotext": shutil.which("pdftotext"),
        "Node": shutil.which("node"),
    }
    missing = [name for name, path in required.items() if not path]
    if missing:
        message = "Real preview dependencies unavailable. " + ", ".join(missing)
        if os.environ.get("SLIDEPOISE_REQUIRE_PREVIEW") == "1":
            pytest.fail(message)
        pytest.skip(message)
    return required


def run(*args):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                            env={**os.environ, "PYTHON": sys.executable}, timeout=120)
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout


def test_actual_office_preview_preserves_order_and_english_chinese_text(tmp_path):
    tools = require_preview_tools()
    cjk_font = "PingFang SC" if sys.platform == "darwin" else "Microsoft YaHei" if sys.platform == "win32" else "Noto Sans CJK SC"
    slides = []
    for index, (title, message) in enumerate([
        ("A clearer decision", "Native text remains editable"),
        ("中文排版与重建", "保留清晰的文字与结构"),
    ], start=1):
        slides.append({"slide_id": f"page-{index}", "dimensions_px": [1600, 900], "background": "#FFFFFF", "objects": [
            {"id": "title", "kind": "textbox", "text": title, "bbox_px": [120, 140, 1320, 120],
             "style": {"font_family": cjk_font, "font_size_pt": 34, "color": "#142E45"}},
            {"id": "body", "kind": "textbox", "text": message, "bbox_px": [120, 330, 1320, 120],
             "style": {"font_family": cjk_font, "font_size_pt": 26, "color": "#243E50"}},
        ]})
    spec = tmp_path / "renderer-fixture.json"
    spec.write_text(json.dumps({"title": "Bilingual renderer fixture", "slides": slides}, ensure_ascii=False), encoding="utf-8")
    powerpoint = tmp_path / "bilingual.pptx"
    run(tools["Node"], str(ROOT / "slidepoise/runtime/js/scene_to_pptx.mjs"), "--input", str(spec), "--output", str(powerpoint))
    output = tmp_path / "preview"
    run(sys.executable, str(RUNTIME), "render-deck-preview", "--pptx", str(powerpoint), "--output-dir", str(output), "--dpi", "96")

    # Extraction reads what Office actually emitted, not the original PPTX XML.
    # Retained PNGs still need host visual review for typography and glyph shape.
    pages = run(tools["pdftotext"], "-layout", str(output / "presentation.pdf"), "-").split("\f")
    assert "A clearer decision" in pages[0]
    assert "Native text remains editable" in pages[0]
    assert "中文排版与重建" in "".join(pages[1].split())
    assert "保留清晰的文字与结构" in "".join(pages[1].split())
    assert "A clearer decision" not in pages[1]
    manifest = json.loads((output / "preview-manifest.json").read_text(encoding="utf-8"))
    assert [page["slide_number"] for page in manifest["slides"]] == [1, 2]
    for page in manifest["slides"]:
        with Image.open(output / page["render"]) as preview:
            assert preview.format == "PNG"
            assert preview.width > preview.height > 0
    with Image.open(output / manifest["contact_sheet"]["path"]) as sheet:
        sheet.verify()
