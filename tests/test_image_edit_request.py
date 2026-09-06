"""Focused edits retain the verified design and detect stale or oversized handoffs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from test_generation_request import compiled_request  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "slidepoise/scripts"), str(ROOT / "slidepoise/runtime/src")]
from prepare_generation import build_request, verify_request
from prepare_image_edit import build_edit_request, verify_edit_request


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def edit_inputs(compiled_request):  # noqa: F811
    candidate = compiled_request.with_name("candidate.png")
    Image.new("RGB", (960, 480), "white").save(candidate)
    changes = compiled_request.with_name("changes.txt")
    changes.write_text("Agent visual review found clipped content. Widen the decision message while preserving its wording.", encoding="utf-8")
    return compiled_request, candidate, changes


def run_edit(inputs, output, *options):
    command = [sys.executable, str(ROOT / "slidepoise/scripts/prepare_image_edit.py")]
    for option, path in zip(("--generation-request", "--candidate", "--changes"), inputs):
        command.extend([option, str(path)])
    return subprocess.run([*command, "--output", str(output), *options], text=True, capture_output=True, check=False)


def test_host_review_can_compile_and_submit_one_bound_edit_without_user_gate(edit_inputs):
    base = verify_request(edit_inputs[0])
    output = edit_inputs[0].with_name("edit-request.json")
    result = run_edit(edit_inputs, output)
    assert result.returncode == 0, result.stderr
    request = verify_edit_request(output)
    assert request["canvas"] == base["canvas"]
    assert request["canvas"]["master_frame_excluded"] is True
    assert request["candidate_dimensions_px"] == [960, 480]
    assert request["prompt"].count(base["prompt"]) == 1
    assert edit_inputs[2].read_text() in request["prompt"]
    assert request["reference_images"][1:] == base["reference_images"]
    assert request["reference_images"][0]["sha256"] == hashlib.sha256(edit_inputs[1].read_bytes()).hexdigest()
    assert request["prompt_sha256"] == hashlib.sha256(request["prompt"].encode()).hexdigest()
    assert request["prompt_character_count"] == len(request["prompt"])
    payload = json.loads(request["prompt"].split("```json", 1)[1].split("```", 1)[0])
    assert payload["deck_design"]["design_id"] == "shared-editorial-system"
    verified = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/prepare_image_edit.py"),
                               "--verify-request", str(output)], capture_output=True, text=True, check=False)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout) == request


@pytest.mark.parametrize("changed", ["candidate.png", "changes.txt", "generation-request.json", "intent.json", "deck.json", "references.png"])
def test_changes_to_pixels_corrections_or_upstream_design_make_edit_stale(edit_inputs, changed):
    output = edit_inputs[0].with_name("edit-request.json")
    write(output, build_edit_request(*edit_inputs))
    path = output.with_name(changed)
    if path.suffix == ".png":
        Image.new("RGB", (60, 40), "black").save(path)
    else:
        path.write_text(path.read_text() + "\n")
    with pytest.raises(SystemExit, match="changed|differs"):
        verify_edit_request(output)


def test_capacity_includes_corrections_and_preserves_existing_output(edit_inputs):
    original = verify_request(edit_inputs[0])
    maximum = len(build_edit_request(*edit_inputs)["prompt"])
    inputs = {name: Path(record["path"]) for name, record in original["input_bindings"].items()}
    contract = json.loads(inputs["contract"].read_text())
    write(edit_inputs[0], build_request(contract, inputs=inputs, max_prompt_chars=maximum))
    request = build_edit_request(*edit_inputs)
    assert request["host_constraints"]["max_prompt_chars"] == maximum
    output = edit_inputs[0].with_name("edit-request.json")
    write(output, request)
    assert verify_edit_request(output) == request
    before = output.read_bytes()
    edit_inputs[2].write_text(edit_inputs[2].read_text() + " Preserve the table.")
    result = run_edit(edit_inputs, output, "--max-prompt-chars", str(maximum + 10000))
    assert result.returncode != 0
    assert "No content was truncated" in result.stderr
    assert output.read_bytes() == before


@pytest.mark.parametrize("field,value", [("prompt", "Draw an unrelated design"), ("canvas", {"master_frame_excluded": False}),
                                         ("reference_images", [])])
def test_edit_handoff_cannot_rewrite_compiled_prompt_canvas_or_attachments(edit_inputs, field, value):
    request = build_edit_request(*edit_inputs)
    request[field] = value
    output = edit_inputs[0].with_name("edit-request.json")
    write(output, request)
    with pytest.raises(SystemExit, match="differs"):
        verify_edit_request(output)


@pytest.mark.parametrize("source", ["candidate.png", "contract.json", "references.png"])
def test_edit_output_cannot_replace_a_bound_source(edit_inputs, source):
    output = edit_inputs[0].with_name(source)
    before = output.read_bytes()
    result = run_edit(edit_inputs, output)
    assert result.returncode != 0
    assert "distinct" in result.stderr
    assert output.read_bytes() == before


def test_edit_requires_an_actual_image_and_a_concrete_correction(edit_inputs):
    edit_inputs[1].write_text("Not an image")
    with pytest.raises(SystemExit, match="Cannot read the candidate"):
        build_edit_request(*edit_inputs)
    Image.new("RGB", (60, 40), "white").save(edit_inputs[1])
    edit_inputs[2].write_text("\n ")
    with pytest.raises(SystemExit, match="changes are empty"):
        build_edit_request(*edit_inputs)
