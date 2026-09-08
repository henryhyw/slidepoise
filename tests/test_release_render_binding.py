"""A fresh review cannot make an old preview represent a changed PowerPoint."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "slidepoise/scripts"))
from collect_release_evidence import render_binding_checks


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("change,field", [("pptx", "source_sha256"), ("render", "render_sha256"), ("page", "slide_number")])
def test_old_or_different_page_render_is_rejected(tmp_path, change, field):
    pptx, render = tmp_path / "deck.pptx", tmp_path / "slide.png"
    pptx.write_bytes(b"original PowerPoint bytes")
    render.write_bytes(b"original preview bytes")
    sidecar = render.with_suffix(".source.json")
    sidecar.write_text(json.dumps({"source_sha256": digest(pptx), "render_sha256": digest(render), "slide_number": 2}))
    assert render_binding_checks(pptx, render, 2) == []
    if change == "pptx":
        pptx.write_bytes(b"revised PowerPoint bytes")
    elif change == "render":
        render.write_bytes(b"different preview bytes")
    assert {"reason": "render_source_binding_mismatch", "field": field} in render_binding_checks(pptx, render, 1 if change == "page" else 2)


def test_render_requires_provenance_and_preserves_bound_diagnostics(tmp_path):
    pptx, render = tmp_path / "deck.pptx", tmp_path / "slide.png"
    pptx.write_bytes(b"PowerPoint")
    render.write_bytes(b"preview")
    assert render_binding_checks(pptx, render, 1)[0]["reason"] == "render_source_binding_missing"
    sidecar = render.with_suffix(".source.json")
    sidecar.write_text("[]")
    assert render_binding_checks(pptx, render, 1)[0]["reason"] == "render_source_binding_invalid"
    evidence = tmp_path / "slide.text-evidence.json"
    evidence.write_text('{"discrepancies": [{"missing_complete_tokens": ["adoption"]}]}')
    sidecar.write_text(json.dumps({"source_sha256": digest(pptx), "render_sha256": digest(render), "slide_number": 1,
                                 "rendered_text": {"path": evidence.name, "sha256": digest(evidence)}}))
    assert render_binding_checks(pptx, render, 1) == []
    evidence.write_text('{"discrepancies": []}')
    assert render_binding_checks(pptx, render, 1) == [{"reason": "rendered_text_evidence_missing_or_changed"}]
