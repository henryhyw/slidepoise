"""Audience notes survive the real reconstruction and native document boundary."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

from test_native_presentation import emit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/runtime/src"))
from slidepoise.reconstruction.contract import build_reconstruction_contract
from slidepoise.reconstruction.scene import build_reconstruction_scene


def test_explicit_speaker_notes_survive_compilation_and_native_zip(tmp_path):
    notes = ["Planning example, not a forecast.\nValidate the 20 paired tasks.",
             "Editable paths do not automatically reattach. 中文 & <context>"]
    measured = {"source": {"path": "accepted.png", "width_px": 1920, "height_px": 1080},
                "entities": [], "upstream_handoff": {"speaker_notes": notes,
                "notes": ["Internal Agent operations must remain private to the work records."]}}
    design = {"full_slide_px": [1920, 1080], "frame": {}}
    contract = build_reconstruction_contract(measured, design)
    scene = build_reconstruction_scene(measured_scene=measured, contract=contract, design=design, slide_id="notes")
    assert contract["speaker_notes"] == scene["speaker_notes"] == notes
    result, output = emit(scene, tmp_path)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("ppt/notesSlides/notesSlide1.xml"))
    text = "\n".join(element.text or "" for element in root.iter()
                     if element.tag.endswith("}t"))
    for line in "\n".join(notes).splitlines():
        assert line in text
    assert text.index("Planning example") < text.index("[SlidePoise sources]")
    assert "accepted.png" in text
    assert "Internal Agent operations" not in text


def test_structured_internal_data_cannot_be_coerced_into_speaker_notes():
    measured = {"source": {"width_px": 1920, "height_px": 1080}, "entities": [],
                "upstream_handoff": {"speaker_notes": [{"approved": True}]}}
    with pytest.raises(ValueError, match="speaker_notes must be an array of strings"):
        build_reconstruction_contract(measured, {"full_slide_px": [1920, 1080]})


def test_direct_scene_rejects_invalid_notes_before_writing_a_document(tmp_path):
    result, output = emit({"dimensions_px": [1920, 1080], "objects": [],
                           "speaker_notes": {"text": "Invalid shape"}}, tmp_path)
    assert result.returncode != 0
    assert "speaker_notes must be an array of strings" in result.stderr
    assert not output.exists()
