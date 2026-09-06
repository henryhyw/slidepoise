"""Candidate normalization uses the same inherited frame as reconstruction."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "slidepoise/scripts/normalize_generation_canvas.py"


def run_normalization(tmp_path, config, *extra):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(tmp_path / "source.png"),
         "--config", str(config_path), "--output", str(tmp_path / "output.png"), *extra],
        capture_output=True, text=True,
    )


def framed_design():
    return {"design": {"full_slide_px": [192, 108], "frame": {
        "header": {"enabled": True, "height_px": 6},
        "footer": {"enabled": True, "height_px": 6},
    }}}


def test_normalization_derives_content_canvas_and_preserves_aspect(tmp_path):
    source = Image.new("RGB", (96, 48), "white")
    source.paste("red", (0, 0, 24, 48))
    source.save(tmp_path / "source.png")
    result = run_normalization(tmp_path, framed_design())
    assert result.returncode == 0, result.stderr
    output = Image.open(tmp_path / "output.png")
    assert output.size == (192, 96)
    assert output.getpixel((20, 48)) == (255, 0, 0)
    assert output.getpixel((75, 48)) == (255, 255, 255)
    assert json.loads(result.stdout)["placed_px"] == [0, 0, 192, 96]


def test_stale_canvas_cannot_replace_a_previous_normalized_target(tmp_path):
    Image.new("RGB", (192, 108), "white").save(tmp_path / "source.png")
    output = tmp_path / "output.png"
    output.write_bytes(b"previous usable target")
    config = framed_design()
    config["derived"] = {"generation_region_px": [192, 108]}
    result = run_normalization(tmp_path, config)
    assert result.returncode != 0
    assert "Rerun resolve_config.py" in result.stderr
    assert output.read_bytes() == b"previous usable target"


def test_host_crop_removes_only_the_authored_frame_region(tmp_path):
    source = Image.new("RGB", (192, 108), "red")
    source.paste("white", (0, 6, 192, 102))
    source.save(tmp_path / "source.png")
    result = run_normalization(tmp_path, framed_design(), "--crop", "0", "6", "192", "96")
    assert result.returncode == 0, result.stderr
    assert Image.open(tmp_path / "output.png").getcolors() == [(192 * 96, (255, 255, 255))]
    assert json.loads(result.stdout)["source_after_crop_px"] == [192, 96]
