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
from prepare_generation import build_brief, build_contract, build_request, build_style_context, generation_reference_images, generation_resource_projection, verify_request
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
    contract["communication_intent"]["reading_context"] = "Read without a presenter"
    contract["communication_intent"]["evidence"] = [{
        "observation": "18 of 24 invited users returned in week two",
        "supports": "Short-term use among the invited cohort",
        "limits": "No observation of paid renewal or longer-term retention",
        "status": "Illustrative observation",
    }]
    contract["communication_intent"]["avoid"] = ["Do not depict paid renewal as verified"]
    contract["profile"]["writing_principles"] = ["Keep stated uncertainty beside the claim it qualifies"]
    contract["profile"]["anti_patterns"] = ["Do not use decorative status badges or glossy gradients"]
    contract["non_negotiable_design"]["semantic_style_tokens"] = {
        "qualified_claim": {"fill": "#F4F3F0", "text_color": "#242321"},
    }
    contract["non_negotiable_design"]["data_visualization"] = {
        "default_series_colors": ["#242321", "#8F8F8F"],
        "gridline_color": "#D8D7D3",
        "chart_title_font": "Georgia",
    }
    contract["resources"]["selected_assets"] = [{"asset_id": "required-mark", "generation_instruction": "Preserve this identity"}]
    prompt = build_brief(contract)
    payload = json.loads(prompt.split("```json", 1)[1].split("```", 1)[0])
    assert payload["communication_intent"] == contract["communication_intent"]
    assert payload["resources"] == generation_resource_projection(contract["resources"])
    assert payload["deck_design"] == contract["deck_design"]["content"]
    assert payload["canvas"] == contract["canvas"]
    for key in ("hard_rules", "style_agency", "visual_principles", "density_guidance", "writing_principles", "anti_patterns"):
        assert payload["profile"][key] == contract["profile"][key]
    for key in ("reasoning_principles", "review_questions"):
        assert key not in payload["profile"]
    assert "explicit_user_visual_requirements" not in payload["non_negotiable_design"]
    design = {**payload["non_negotiable_design"],
              "explicit_user_visual_requirements": payload["communication_intent"]["explicit_user_visual_requirements"]}
    assert design == contract["non_negotiable_design"]
    for key in ("writing_principles", "anti_patterns", "semantic_style_tokens", "data_visualization"):
        assert prompt.count(f'"{key}"') == 1
    assert prompt.count('"communication_intent"') == 1
    assert "continue without per-slide approval" not in prompt


def test_selection_deliberation_stays_with_host_and_asset_requirements_reach_model(tmp_path: Path) -> None:
    config, intent, resources = generic_generation_inputs(tmp_path)
    resources["selection_reasoning"] = {
        "icons": {
            "communication_roles": ["Distinguish source review from release approval"],
            "candidates_inspected": ["file-search", "shield-check"],
            "decision": "Provisional rejection of all icons pending comparison with source material.",
        }
    }
    resources["selected_assets"] = [
        {"asset_id": "project-mark", "canonical_file": str(tmp_path / "mark.svg"),
         "generation_description": "Exact project mark", "user_required": True,
         "intrinsic_aspect_ratio": 1.0},
        {"asset_id": "stage-symbol", "canonical_file": str(tmp_path / "stage.svg"),
         "generation_description": "Optional source-review symbol"},
        {"asset_id": "source-diagram", "canonical_file": str(tmp_path / "diagram.png"),
         "generation_description": "Required evidence diagram", "required_for_slide": True},
    ]
    contract = build_contract(config, intent, resources)
    prompt = build_brief(contract)
    payload = json.loads(prompt.split("```json", 1)[1].split("```", 1)[0])
    assert contract["resources"]["selection_reasoning"] == resources["selection_reasoning"]
    assert "selection_reasoning" not in payload["resources"]
    assert resources["selection_reasoning"]["icons"]["decision"] not in prompt
    assets = {item["asset_id"]: item for item in payload["resources"]["generation_asset_descriptions"]}
    assert assets["project-mark"]["required_for_slide"] is True
    assert assets["project-mark"]["user_required"] is True
    assert assets["project-mark"]["require_exact_identity"] is True
    assert assets["project-mark"]["intrinsic_aspect_ratio"] == 1.0
    assert assets["stage-symbol"]["required_for_slide"] is False
    assert assets["stage-symbol"]["generation_description"] == "Optional source-review symbol"
    assert assets["source-diagram"]["required_for_slide"] is True
    assert assets["source-diagram"]["user_required"] is False


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


@pytest.mark.parametrize("width,height", [(400, 100), (100, 400)])
@pytest.mark.parametrize("representation", ["individual_attachments", "full_context_sheet"])
def test_svg_asset_context_prepares_bound_transparent_raster_transport(tmp_path, width, height, representation):
    from make_asset_contact_sheet import collect_resource_review_items

    config, intent, resources = generic_generation_inputs(tmp_path)
    config["resolved_profile"]["hard_rules"]["asset_vocabulary"] = {
        "mode": "open", "generation_representation": representation}
    source = tmp_path / "brand-mark.svg"
    original = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
                f'<rect x="10" y="10" width="{width - 20}" height="{height - 20}" fill="#123456"/></svg>')
    source.write_text(original)
    resources["selected_assets"] = [{"asset_id": "brand-mark", "canonical_file": str(source),
        "generation_description": "Use the exact project mark", "user_required": True, "source": "project_repository"}]
    with pytest.raises(SystemExit, match="SVG attachment needs a prepared PNG preview"):
        generation_reference_images({"resources": resources})
    for name, value in (("config", config), ("intent", intent), ("draft", resources)):
        write(tmp_path / f"{name}.json", value)
    prepared = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/prepare_resource_context.py"),
        "--config", str(tmp_path / "config.json"), "--intent", str(tmp_path / "intent.json"),
        "--resources", str(tmp_path / "draft.json"), "--output-resources", str(tmp_path / "resources.json"),
        "--sheet", str(tmp_path / "context.png"), "--manifest", str(tmp_path / "context.json")],
        capture_output=True, text=True)
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    resolved = json.loads((tmp_path / "resources.json").read_text())
    asset = resolved["selected_assets"][0]
    assert asset["canonical_file"] == str(source)
    preview = Path(asset["generation_preview"]["path"])
    preview_bytes = preview.read_bytes()
    with Image.open(preview) as image:
        assert image.format == "PNG" and image.mode == "RGBA"
        assert image.width / image.height == width / height
        assert max(image.size) == 1024
        assert image.getpixel((0, 0))[3] == 0
        assert image.getpixel((image.width // 2, image.height // 2)) == (18, 52, 86, 255)
    assert collect_resource_review_items(resolved)[0]["role"].startswith("Required asset.")
    asset["source"] = "current_chat_upload"
    assert collect_resource_review_items(resolved)[0]["role"].startswith("User upload.")

    command = [sys.executable, str(ROOT / "slidepoise/scripts/prepare_generation.py")]
    for name, path in (("config", "config.json"), ("intent", "intent.json"), ("resources", "resources.json"),
                       ("contract", "contract.json"), ("brief", "brief.md")):
        command += ["--" + name, str(tmp_path / path)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    request_path = tmp_path / "generation-request.json"
    request = verify_request(request_path)
    if representation == "individual_attachments":
        attachment = next(item for item in request["reference_images"] if item["id"] == "brand-mark")
        assert attachment["path"] == str(preview)
        assert attachment["sha256"] == hashlib.sha256(preview_bytes).hexdigest()
        assert attachment["source"] == {"path": str(source.resolve()), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    else:
        assert [item["id"] for item in request["reference_images"]] == ["generation-context"]
    source.write_text(original.replace("#123456", "#ABCDEF"))
    with pytest.raises(SystemExit, match="SVG preview source changed"):
        verify_request(request_path)
    source.write_text(original)
    Image.new("RGBA", (1024, 256), "red").save(preview)
    with pytest.raises(SystemExit, match="SVG preview changed"):
        verify_request(request_path)
    # Recompilation must not bless altered pixels under the old source binding.
    stale = subprocess.run(command, capture_output=True, text=True)
    assert stale.returncode != 0 and "SVG preview changed" in stale.stderr


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
