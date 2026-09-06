"""Generation inputs reach one fresh request with consistent canvas geometry."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
import pytest

from test_skill_integration import generic_generation_inputs

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "slidepoise/scripts"), str(ROOT / "slidepoise/runtime/src")]
from prepare_generation import build_brief, build_contract, build_request, build_style_context, generation_reference_images, verify_request
from slidepoise.canvas import derive_canvas, validate_derived_canvas
from slidepoise.reconstruction.contract import build_reconstruction_contract
from slidepoise.reconstruction.scene import build_reconstruction_scene


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def compiled_request(tmp_path):
    config, intent, resources = generic_generation_inputs(tmp_path)
    Image.new("RGB", (60, 40), "white").save(tmp_path / "references.png")
    resources["generation_context_sheet"] = {"path": str(tmp_path / "references.png")}
    deck = {"schema_version": "1.0", "design_id": "shared-editorial-system", "frame_source": "resolved.json#/design/frame",
            "repeated_roles": {"claim_title": {"font_family": "Arial", "font_size_pt": 30}},
            "allowed_variations": ["Opening may use a separate display role"],
            "reference_images": [{"id": "calibration", "path": "references.png", "purpose": "Authored recurring role example"}],
            "cross_slide_review_focus": ["Peer claim titles"]}
    for name, value in (("config", config), ("intent", intent), ("resources", resources), ("deck", deck)):
        write(tmp_path / f"{name}.json", value)
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/prepare_generation.py"),
                             "--config", str(tmp_path / "config.json"), "--intent", str(tmp_path / "intent.json"),
                             "--resources", str(tmp_path / "resources.json"), "--deck-design", str(tmp_path / "deck.json"),
                             "--contract", str(tmp_path / "contract.json"), "--brief", str(tmp_path / "brief.md")],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return tmp_path / "generation-request.json"


def test_request_is_the_compiled_prompt_with_bound_shared_design_and_images(compiled_request):
    request = verify_request(compiled_request)
    assert request["prompt"] == (compiled_request.parent / "brief.md").read_text()
    payload = json.loads(request["prompt"].split("```json", 1)[1].split("```", 1)[0])
    assert payload["deck_design"]["repeated_roles"]["claim_title"] == {"font_family": "Arial", "font_size_pt": 30}
    assert request["prompt_character_count"] == len(request["prompt"])
    assert request["canvas"]["master_frame_excluded"] is True
    assert request["reference_images"][0]["sha256"]
    assert len(request["reference_images"]) == 1
    assert "deck_design" in request["input_bindings"]


def test_model_prompt_preserves_complete_visual_inputs_once(compiled_request):
    contract = json.loads((compiled_request.parent / "contract.json").read_text())
    # Preserve future authored fields too, without an allowlist of slide facts.
    contract["communication_intent"]["qualifications"] = ["Evidence is preliminary", "保留原始限定条件"]
    contract["resources"]["selected_assets"] = [{"asset_id": "required-mark", "generation_instruction": "Preserve this identity"}]
    prompt = build_brief(contract)
    payload = json.loads(prompt.split("```json", 1)[1].split("```", 1)[0])
    assert payload["communication_intent"] == contract["communication_intent"]
    assert payload["resources"] == {key: value for key, value in contract["resources"].items() if key != "style_context"}
    assert payload["deck_design"] == contract["deck_design"]["content"]
    assert payload["canvas"] == contract["canvas"]
    for key in ("hard_rules", "style_agency", "visual_principles", "writing_principles", "anti_patterns", "density_guidance"):
        assert payload["profile"][key] == contract["profile"][key]
    design = {**payload["non_negotiable_design"],
              "explicit_user_visual_requirements": payload["communication_intent"]["explicit_user_visual_requirements"]}
    assert design == contract["non_negotiable_design"]
    assert prompt.count('"communication_intent"') == 1
    assert "continue without per-slide approval" not in prompt


def test_grammar_only_components_remain_prompt_guidance_without_an_image(compiled_request):
    contract = json.loads((compiled_request.parent / "contract.json").read_text())
    contract["resources"]["asset_vocabulary_policy"]["generation_representation"] = "individual_attachments"
    component = {"component_id": "decision-table", "resource_form": "grammar_only", "grammar": {"rows": "One row per decision"}}
    contract["resources"]["selected_components"] = [component]
    images = generation_reference_images(contract)
    assert len(images) == 1 and images[0]["id"] == "generation-context"
    assert component["grammar"]["rows"] in build_brief(contract)


def test_full_resolution_references_are_ordered_and_fresh_under_context_sheet_policy(compiled_request):
    directory = compiled_request.parent
    config = json.loads((directory / "config.json").read_text())
    config["resolved_profile"]["hard_rules"]["asset_vocabulary"] = {
        "mode": "closed", "generation_representation": "full_context_sheet",
        "attach_selected_asset_files_to_image_generation": False}
    resources = json.loads((directory / "resources.json").read_text())
    resources["style_context"] = build_style_context(config)
    references = []
    for name, color, direct in (("type-reference", "blue", True), ("index-only", "green", False), ("structure-reference", "red", True)):
        path = directory / f"{name}.png"
        Image.new("RGB", (800, 400), color).save(path)
        references.append({"id": name, "canonical_file": str(path), "reason": "Inspect authored hierarchy",
                           "full_resolution_attachment": direct})
    resources["selected_visual_references"] = references
    asset = directory / "canonical-asset.png"
    Image.new("RGB", (800, 400), "orange").save(asset)
    resources["selected_assets"] = [{"asset_id": "identity", "canonical_file": str(asset), "generation_description": "Exact identity asset"}]
    write(directory / "config.json", config)
    write(directory / "resources.json", resources)
    original = json.loads(compiled_request.read_text())
    command = [sys.executable, str(ROOT / "slidepoise/scripts/prepare_generation.py")]
    for name, binding in original["input_bindings"].items():
        command.extend(["--" + name.replace("_", "-"), binding["path"]])
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    request = verify_request(compiled_request)
    assert [item["id"] for item in request["reference_images"]] == ["generation-context", "type-reference", "structure-reference"]
    for attachment in request["reference_images"][1:]:
        path = directory / f"{attachment['id']}.png"
        assert attachment["path"] == str(path.resolve())
        assert attachment["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    # Changing the original invalidates the call even with the same tiny sheet.
    Image.new("RGB", (800, 400), "purple").save(directory / "type-reference.png")
    with pytest.raises(SystemExit, match="differs"):
        verify_request(compiled_request)


@pytest.mark.parametrize("value", ["true", 1])
def test_full_resolution_attachment_requires_an_explicit_boolean(tmp_path, value):
    config, intent, resources = generic_generation_inputs(tmp_path)
    resources["selected_visual_references"] = [{"id": "reference", "canonical_file": "original.png", "reason": "Typography",
                                               "full_resolution_attachment": value}]
    with pytest.raises(SystemExit, match="full_resolution_attachment must be boolean"):
        build_contract(config, intent, resources)


def test_host_capacity_is_explicit_and_never_truncates_or_overwrites(compiled_request):
    original = verify_request(compiled_request)
    inputs = {name: Path(record["path"]) for name, record in original["input_bindings"].items()}
    contract = json.loads(inputs["contract"].read_text())
    maximum = len(original["prompt"])
    request = build_request(contract, inputs=inputs, max_prompt_chars=maximum)
    assert request["prompt"] == original["prompt"]
    assert request["host_constraints"] == {"max_prompt_chars": maximum}
    write(compiled_request, request)
    assert verify_request(compiled_request) == request
    before = {path: path.read_bytes() for path in [compiled_request, inputs["contract"], inputs["brief"]]}
    command = [sys.executable, str(ROOT / "slidepoise/scripts/prepare_generation.py")]
    for name, path in inputs.items():
        command.extend(["--" + name.replace("_", "-"), str(path)])
    result = subprocess.run([*command, "--max-prompt-chars", str(maximum - 1)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "No content was truncated" in result.stderr
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("maximum", [True, 0, -1, 1.5, "32000"])
def test_invalid_host_capacity_is_a_structural_error(compiled_request, maximum):
    request = json.loads(compiled_request.read_text())
    request["host_constraints"]["max_prompt_chars"] = maximum
    write(compiled_request, request)
    with pytest.raises(SystemExit, match="positive integer"):
        verify_request(compiled_request)


@pytest.mark.parametrize("name", ["config.json", "intent.json", "resources.json", "deck.json"])
def test_changed_generation_inputs_invalidate_the_request(compiled_request, name):
    path = compiled_request.parent / name
    path.write_text(path.read_text() + "\n")
    with pytest.raises(SystemExit, match="input changed"):
        verify_request(compiled_request)


def test_changed_reference_pixels_invalidate_the_request(compiled_request):
    Image.new("RGB", (60, 40), "black").save(compiled_request.parent / "references.png")
    with pytest.raises(SystemExit, match="differs"):
        verify_request(compiled_request)


def test_a_rewritten_prompt_cannot_silently_replace_the_compiled_brief(compiled_request):
    request = json.loads(compiled_request.read_text())
    request["prompt"] = "Draw a different full-slide canvas."
    write(compiled_request, request)
    with pytest.raises(SystemExit, match="compiled brief"):
        verify_request(compiled_request)


def test_equal_height_frame_content_changes_still_invalidate_style_context(tmp_path):
    config, intent, resources = generic_generation_inputs(tmp_path)
    assert build_style_context(config)["frame"] == config["design"]["frame"]
    config["design"]["frame"]["header"]["left_text"] = "A changed inherited header"
    with pytest.raises(SystemExit, match="Style changed"):
        build_contract(config, intent, resources)


def test_generation_refuses_stale_derived_geometry_even_with_fresh_style_context(tmp_path):
    config, intent, resources = generic_generation_inputs(tmp_path)
    config["derived"]["generation_region_px"][1] -= 20
    resources["style_context"] = build_style_context(config)
    with pytest.raises(SystemExit, match="disagrees with design.frame"):
        build_contract(config, intent, resources)


def test_content_only_source_is_translated_below_frame_without_squashing():
    design = {"full_slide_px": [1920, 1080], "frame": {"header": {"enabled": True, "height_px": 41},
                                                       "footer": {"enabled": True, "height_px": 41}}}
    measured = {"source": {"width_px": 960, "height_px": 499}, "entities": []}
    contract = build_reconstruction_contract(measured, design)
    assert contract["coordinate_transform_to_full_slide"] == {"scale_xy": [2, 2], "translation_px": [0, 41]}
    measured["source"] = {"width_px": 1920, "height_px": 1080}
    with pytest.raises(ValueError, match="cannot stretch"):
        build_reconstruction_contract(measured, design)


def test_source_pixel_rounding_is_not_an_aspect_ratio_failure():
    result = build_reconstruction_contract({"source": {"width_px": 1672, "height_px": 941}, "entities": []},
                                          {"full_slide_px": [1920, 1080]})
    assert result["generation_region"]["dimensions_px"] == [1920, 1080]


def test_reusing_a_contract_cannot_bypass_the_frame_transform_boundary():
    design = {"full_slide_px": [1920, 1080], "frame": {"header": {"enabled": True, "height_px": 41},
                                                       "footer": {"enabled": True, "height_px": 41}}}
    measured = {"source": {"width_px": 960, "height_px": 499}, "entities": []}
    contract = build_reconstruction_contract(measured, design)
    contract["coordinate_transform_to_full_slide"]["scale_xy"][1] = 1.8
    with pytest.raises(ValueError, match="coordinate_transform_to_full_slide disagrees"):
        build_reconstruction_scene(measured_scene=measured, contract=contract, design=design, slide_id="stale")


@pytest.mark.parametrize("bad", [True, "41", -1, 1.5, float("nan")])
def test_frame_dimensions_cannot_be_silently_coerced(bad):
    design = {"full_slide_px": [1920, 1080], "frame": {"header": {"enabled": True, "height_px": bad}}}
    with pytest.raises(ValueError, match="integer"):
        derive_canvas(design)


def test_derived_validation_uses_the_same_source_as_reconstruction():
    config = {"design": {"full_slide_px": [1920, 1080], "frame": {"header": {"enabled": True, "height_px": 50}}}}
    config["derived"] = derive_canvas(config["design"])
    assert validate_derived_canvas(config) == config["derived"]
    old = copy.deepcopy(config["derived"])
    config["design"]["frame"]["header"]["height_px"] = 60
    with pytest.raises(ValueError, match="disagrees"):
        validate_derived_canvas(config)
    assert config["derived"] == old
