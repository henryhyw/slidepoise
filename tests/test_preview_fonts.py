from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "slidepoise/scripts"))
import slidepoise_runtime as runtime


def test_missing_font_config_fails_before_renderer(tmp_path):
    args = runtime.parser().parse_args(["render-preview", "--pptx", "input.pptx", "--output", str(tmp_path / "out.png"), "--font-config", str(tmp_path / "missing.conf")])
    with pytest.raises(SystemExit, match="Fontconfig file does not exist"):
        runtime.command_render_preview(args)


def test_font_config_is_scoped_to_renderer(tmp_path, monkeypatch):
    config = tmp_path / "fonts.conf"
    config.write_text("<fontconfig/>")
    source = tmp_path / "input.pptx"
    source.write_bytes(b"renderer input fixture")
    args = runtime.parser().parse_args(["render-preview", "--pptx", str(source), "--output", str(tmp_path / "out.png"), "--font-config", str(config)])
    calls = []
    monkeypatch.setattr(runtime.shutil, "which", lambda name: name)

    def command(argv, *, env=None):
        calls.append((argv, env))
        if "--outdir" in argv:
            (Path(argv[argv.index("--outdir") + 1]) / "input.pdf").write_bytes(b"test pdf")
        else:
            Path(argv[-1] + ".png").write_bytes(b"test render")

    monkeypatch.setattr(runtime, "run_checked", command)
    monkeypatch.setenv("FONTCONFIG_FILE", "previous.conf")
    runtime.command_render_preview(args)
    assert calls[0][1]["FONTCONFIG_FILE"] == str(config.resolve())
    assert runtime.os.environ["FONTCONFIG_FILE"] == "previous.conf"
    assert args.output.read_bytes() == b"test render"


def test_macos_preview_discovers_system_fonts_without_global_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.sys, "platform", "darwin")
    monkeypatch.setattr(runtime.Path, "is_dir", lambda self: True)
    monkeypatch.delenv("FONTCONFIG_FILE", raising=False)
    env = {}
    evidence = runtime.preview_font_environment(env, tmp_path)
    root = ET.parse(env["FONTCONFIG_FILE"]).getroot()
    assert "/System/Library/Fonts" in [item.text for item in root.findall("dir")]
    assert root.find("cachedir").text == str(tmp_path / "font-cache")
    assert evidence["fontconfig_source"] == "macos_system_font_directories"
    assert "FONTCONFIG_FILE" not in runtime.os.environ


def test_preview_preserves_explicit_font_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.sys, "platform", "darwin")
    config = tmp_path / "chosen.conf"
    config.write_text("<fontconfig/>")
    env = {"FONTCONFIG_FILE": str(config)}
    evidence = runtime.preview_font_environment(env, tmp_path)
    assert env == {"FONTCONFIG_FILE": str(config)}
    assert evidence["fontconfig_source"] == "configured"
    assert evidence["fontconfig_sha256"]
    assert not (tmp_path / "preview-fonts.conf").exists()
