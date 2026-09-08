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


def test_office_composites_transparent_artwork_on_light_and_dark_backgrounds(tmp_path):
    tools = require_preview_tools()
    from PIL import ImageDraw
    import hashlib
    import io
    import zipfile

    asset = Image.new('RGBA', (400, 400), (255, 0, 255, 0))
    draw = ImageDraw.Draw(asset)
    draw.rectangle((100, 100, 299, 299), fill=(230, 90, 40, 128))
    draw.rectangle((150, 150, 249, 249), fill=(230, 90, 40, 255))
    source = tmp_path / 'layer.png'
    asset.save(source)
    slides = []
    backgrounds = ['#FAF8F4', '#202630']
    for index, background in enumerate(backgrounds):
        slides.append({'slide_id': f'alpha-{index}', 'dimensions_px': [1600, 900], 'background': background, 'objects': [
            {'id': 'art', 'kind': 'image', 'bbox_px': [600, 240, 400, 400], 'source_path': str(source),
             'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'z': 1},
            {'id': 'title', 'kind': 'textbox', 'bbox_px': [120, 80, 1360, 100], 'text': 'Artwork retains its transparency',
             'style': {'font_family': 'Arial', 'font_size_pt': 32, 'color': '#222222' if index == 0 else '#FFFFFF'}, 'z': 2},
            {'id': 'caption', 'kind': 'textbox', 'bbox_px': [120, 720, 1360, 80], 'text': 'Native text and image layers remain separate',
             'style': {'font_family': 'Arial', 'font_size_pt': 20, 'color': '#222222' if index == 0 else '#FFFFFF'}, 'z': 2},
        ]})
    spec = tmp_path / 'alpha-scenes.json'
    spec.write_text(json.dumps({'slides': slides}))
    pptx = tmp_path / 'alpha.pptx'
    run(tools['Node'], str(ROOT / 'slidepoise/runtime/js/scene_to_pptx.mjs'), '--input', str(spec), '--output', str(pptx))
    preview = tmp_path / 'preview'
    run(sys.executable, str(RUNTIME), 'render-deck-preview', '--pptx', str(pptx), '--output-dir', str(preview), '--dpi', '96')
    manifest = json.loads((preview / 'preview-manifest.json').read_text())
    for entry, background in zip(manifest['slides'], backgrounds):
        image = Image.open(preview / entry['render']).convert('RGB')
        rgb = tuple(int(background[i:i+2], 16) for i in (1, 3, 5))
        for x, y, expected in [
            (640, 280, rgb),
            (720, 360, tuple(round((fg * 128 + bg * 127) / 255) for fg, bg in zip((230, 90, 40), rgb))),
            (800, 440, (230, 90, 40)),
        ]:
            actual = image.getpixel((round(x * image.width / 1600), round(y * image.height / 900)))
            assert max(abs(a - b) for a, b in zip(actual, expected)) <= 3, (actual, expected)
    with zipfile.ZipFile(pptx) as archive:
        media = [name for name in archive.namelist() if name.startswith('ppt/media/') and name.endswith('.png')]
        assert any(Image.open(io.BytesIO(archive.read(name))).convert('RGBA').tobytes() == asset.tobytes() for name in media)
    text = run(tools['pdftotext'], str(preview / 'presentation.pdf'), '-')
    assert text.count('Native text and image layers remain separate') == 2
