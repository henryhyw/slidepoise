"""The normal installation and measurement route require no segmentation model."""
from __future__ import annotations

import builtins
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from framework import installer
from framework.cli import parser
from webapp.server import runtime_health

ROOT = Path(__file__).resolve().parents[1]


def test_setup_and_console_health_do_not_install_or_load_segmentation(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    imported = builtins.__import__

    def without_models(name, *args, **kwargs):
        assert name.split(".")[0] not in {"torch", "torchvision", "sam2"}, name
        return imported(name, *args, **kwargs)

    def unexpected_install(*args, **kwargs):
        raise AssertionError("Setup attempted an unexpected install or download")

    monkeypatch.setattr(builtins, "__import__", without_models)
    monkeypatch.setattr(subprocess, "run", unexpected_install)
    monkeypatch.setattr(urllib.request, "urlopen", unexpected_install)
    result = installer.setup(install_skill=False, install_node=False)
    config = json.loads((tmp_path / "home/config.json").read_text())
    assert config["measurement"]["engine"] == "OpenCV"
    assert config["measurement"]["segmentation"]["mode"] == "never"
    assert "sam" not in result
    assert not (tmp_path / "home/models").exists()
    assert not (tmp_path / "home/install-status/sam.json").exists()
    health = {entry["name"]: entry for entry in runtime_health()}
    assert health["OpenCV"]["available"]
    assert set(health) == {"Python", "OpenCV", "Node", "PptxGenJS", "LibreOffice", "Poppler"}
    # Previously copied setup commands continue to work, without advertising the obsolete option.
    assert parser().parse_args(["setup", "--skip-sam"]).command == "setup"
    assert "sam" not in parser().format_help().lower()


def test_default_irregular_object_measurement_keeps_opencv_evidence(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(ROOT / "slidepoise/runtime/scripts"))
    import measure_visual_scene
    import sam_optional

    def unexpected_model(*args, **kwargs):
        raise AssertionError("Default measurement attempted to load a segmentation model")

    monkeypatch.setattr(sam_optional, "resolve_device", unexpected_model)
    monkeypatch.setattr(sam_optional, "run", unexpected_model)
    config = json.loads((ROOT / "framework/defaults/slidepoise-config.json").read_text())
    # Even a retained checkpoint and eligible legacy entity do not enable the default route.
    checkpoint = tmp_path / "existing-checkpoint.pt"
    checkpoint.write_bytes(b"not loaded")
    config["measurement"]["segmentation"]["checkpoint"] = str(checkpoint)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    target = Image.new("RGB", (120, 100), "white")
    ImageDraw.Draw(target).polygon([(20, 20), (75, 14), (98, 52), (63, 85), (25, 65)], fill="#186A94")
    image = tmp_path / "target.png"
    target.save(image)
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps({"entities": [{
        "id": "irregular-art", "kind": "image", "geometry_policy": "opencv_visible",
        "bbox_hint": [0, 0, 120, 100], "segmentation_role": "photo_subject",
        "segmentation_preference": "sam_if_available",
    }]}))
    output = tmp_path / "measurement"
    monkeypatch.setattr(sys, "argv", ["measure_visual_scene", str(image), "--semantic-map", str(semantic),
                        "--config", str(config_path), "--output-dir", str(output)])
    measure_visual_scene.main()
    measured = json.loads((output / "slide_entities.json").read_text())
    segmentation = measured["runtime"]["segmentation"]
    assert segmentation["executed"] is False
    assert segmentation["selected_entity_ids"] == []
    entity = measured["entities"][0]["measurement"]
    assert entity["mask_source"] == "opencv"
    x, y, width, height = entity["visible_bbox"]["px"]
    assert 20 <= x < 60 < x + width <= 99
    assert 14 <= y < 50 < y + height <= 86
    assert entity["contours_px"]
    crop = Image.open(entity["image_object"]["screenshot_crop_absolute"])
    assert np.array_equal(np.array(crop), np.array(target)[y:y + height, x:x + width])
    assert (output / "debug_overlay.png").is_file()
    assert "SAM" not in (output / "report.md").read_text()
    assert "sam" not in json.loads(capsys.readouterr().out)
