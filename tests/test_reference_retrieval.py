"""Source restrictions and per-slide recall remain distinct from host selection."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "slidepoise/scripts"), str(ROOT / "slidepoise/runtime/src")]
from prepare_generation import augment_profile_core_references
from slidepoise.reference_retrieval import digest, retrieve, validate_host_selection


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def library(tmp_path):
    catalog = tmp_path / "profile" / "catalog.json"
    config = write(tmp_path / "resolved.json", {"resolved_profile": {"profile_id": "test"},
                   "libraries": {"visual_references": {"catalog": str(catalog)}}})
    intent = write(tmp_path / "intent.json", {"communication_job": "compare options", "role": "comparison",
                                            "relationships": ["parallel comparison"]})
    items = {}

    def add(identifier, *, color="blue", **metadata):
        record = {"id": identifier, "name": identifier, "path": f"{identifier}.png",
                  "roles": ["comparison"], "source": "https://example.org/report.pdf", "source_page": 2,
                  "provenance": {"generated_reference": False, "source_type": "published_document"}, **metadata}
        items[identifier] = record
        catalog.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (200, 100), color).save(catalog.parent / f"{identifier}.png")
        write(catalog, {"items": items})
        return record

    def run(**kwargs):
        return retrieve(config, intent, tmp_path / "candidates.json", tmp_path / "candidates.png", **kwargs)

    return tmp_path, catalog, config, intent, items, add, run


def ids(result):
    return [record["id"] for record in result["candidates"]]


def test_authentic_default_rejects_generated_conflicting_and_unknown_provenance(library):
    _, _, _, _, _, add, run = library
    add("public")
    add("private", source="User conversation file", provenance={"generated_reference": False,
                                                               "source_type": "user_private_document"})
    add("generated", provenance={"generated_reference": True})
    add("conflicting", generated_reference=False, provenance={"generated_source": "true"})
    add("unknown", provenance={"provider": "user_or_agent_added"})
    add("missing-page", source_page=None)
    add("declared-public-only", provenance={"source_type": "published_document"})
    assert set(ids(run())) == {"public", "private"}
    assert "unknown" in ids(run(authenticity="exclude-generated"))
    assert "generated" not in ids(run(authenticity="exclude-generated"))
    assert len(ids(run(authenticity="any"))) == 7


def test_query_uses_per_slide_structure_and_preserves_arbitrary_metadata(library):
    _, _, _, intent, _, add, run = library
    add("comparison", roles=["comparison"], relationships=["parallel comparison"],
        future_metadata={"evidence_topology": "decision alternatives"})
    add("journey", roles=["process"], layout=["sequence"], relationships=["actor handoff"])
    add("wordy", roles=[], extracted_text="comparison options parallel " * 1000)
    first = run()
    assert ids(first)[0] == "comparison"
    assert first["candidates"][0]["metadata"]["future_metadata"] == {"evidence_topology": "decision alternatives"}
    assert "relationships" in first["candidates"][0]["matched_fields"]
    write(intent, {"communication_job": "explain process", "role": "process", "relationships": ["actor handoff"]})
    second = run()
    assert ids(second) == ["journey"]
    assert second["query_fields"] == ["communication_job", "relationships", "role"]
    assert "selected_visual_references" not in second
    assert second["reference_retrieval"]["selection_mode"] == "host_selected"


def test_asset_boundaries_missing_corrupt_and_private_roots(library):
    root, catalog, _, _, items, add, run = library
    private = root / "private"
    private.mkdir()
    outside = private / "source.png"
    Image.new("RGB", (50, 50), "green").save(outside)
    add("traversal", path="../private/source.png")
    add("absolute", path=str(outside))
    add("symlink", path="link.png")
    (catalog.parent / "link.png").symlink_to(outside)
    add("remote", path="https://example.org/slide.png")
    add("missing", path="absent.png")
    add("broken", path="broken.png")
    (catalog.parent / "broken.png").write_text("invalid bitmap")
    assert ids(run()) == []
    reasons = {entry["id"]: entry["reason"] for entry in run()["omitted"]}
    assert reasons == {"traversal": "preview_outside_allowed_roots", "absolute": "preview_outside_allowed_roots",
                       "symlink": "preview_outside_allowed_roots", "remote": "preview_path_must_be_local",
                       "missing": "preview_missing", "broken": "preview_unreadable"}
    assert set(ids(run(asset_roots=[private]))) == {"absolute", "symlink", "traversal"}
    assert items["absolute"]["path"] == str(outside)


def test_architecture_intent_outranks_long_generic_content_overlap(library):
    _, _, _, intent, _, add, run = library
    add("architecture", roles=["architecture"], layout=["system architecture"], relationships=["data flow"])
    add("financial", roles=["comparison", "evidence"], layout=["claims", "cover", "content"],
        description="claim evidence asserted cover content intent review booking settle finance " * 200)
    write(intent, {"information_structure": {"type": "system architecture"},
                   "audience_question": "Show system boundaries and data inputs",
                   "required_content": [{"role": "main claim", "text": "review booking settle finance"}],
                   "visual_obligations": ["claim evidence asserted cover content " * 200]})
    result = run()
    assert ids(result)[0] == "architecture"
    assert result["candidates"][0]["focus_structural_match_count"] == 2
    assert "asserted" not in result["query_terms"]
    assert "claim" not in result["query_terms"]


def test_durable_exclusions_survive_renaming_and_family_aliases(library):
    _, catalog, _, _, _, add, run = library
    add("old-name", source_family="rejected-deck")
    add("new-name", source_family="rejected-deck")
    add("keep", color="green", source_family="new-deck")
    checksum = digest(catalog.parent / "old-name.png")
    assert ids(run(exclusions={"sha256": [checksum]})) == ["keep"]
    assert ids(run(exclusions={"source_families": ["rejected-deck"]})) == ["keep"]
    assert set(ids(run(exclude_ids=["old-name"]))) == {"new-name", "keep"}
    assert "old-name" not in ids(run(exclusions={"canonical_paths": [str(catalog.parent / "old-name.png")]}))
    with pytest.raises(ValueError, match="Unknown exclusion"):
        run(exclusions={"typo_ids": ["old-name"]})


def test_explicit_catalog_scope_and_host_eligibility(library):
    root, _, _, _, _, add, run = library
    add("eligible")
    add("cover", retrieval_eligible=False)
    extra = root / "another-profile" / "catalog.json"
    extra.parent.mkdir()
    Image.new("RGB", (40, 40), "green").save(extra.parent / "other.png")
    write(extra, {"items": {"other": {"id": "other", "path": "other.png", "roles": ["comparison"],
                                     "source": "Private slide", "source_page": 1,
                                     "provenance": {"generated_reference": False}}}})
    assert ids(run()) == ["eligible"]
    assert set(ids(run(extra_catalogs=[extra]))) == {"eligible", "other"}
    assert set(ids(run(include_ineligible=True))) == {"eligible", "cover"}


def test_index_rebuild_and_output_collision_protection(library):
    root, catalog, config, intent, items, add, run = library
    add("current")
    assert ids(run()) == ["current"]
    items["current"]["provenance"]["generated_reference"] = True
    write(catalog, {"items": items})
    assert ids(run()) == []
    with pytest.raises(ValueError, match="cannot overwrite input"):
        retrieve(config, intent, catalog, root / "sheet.png")
    unrelated = root / "unrelated.sqlite"
    unrelated.write_text("User data")
    with pytest.raises(ValueError, match="unrelated index"):
        run(index_path=unrelated)
    assert unrelated.read_text() == "User data"


def test_contact_sheet_contains_actual_candidate_pixels_and_empty_results(library):
    _, _, _, intent, _, add, run = library
    add("actual", color=(12, 34, 234))
    result = run()
    with Image.open(result["contact_sheet"]["path"]) as sheet:
        assert sheet.getpixel((260, 210)) == (12, 34, 234)
    write(intent, {"role": "unmatchedword"})
    result = run()
    assert result["contact_sheet"]["candidate_count"] == 0
    assert result["matching_candidate_count"] == 0


def test_host_selection_cannot_reintroduce_generated_or_excluded_references(library):
    _, catalog, _, _, items, add, run = library
    add("good")
    add("generated", provenance={"generated_reference": True})
    result = run(exclude_ids=["rejected"])
    resources = {"reference_retrieval": result["reference_retrieval"], "selected_visual_references": []}
    profile = {"always_attach_visual_references": ["generated"]}
    libraries = {"visual_references": {"catalog": str(catalog)}}
    assert augment_profile_core_references(profile, resources, libraries)["selected_visual_references"] == []
    resources["selected_visual_references"] = [{**result["candidates"][0], "reason": "Host-inspected parallel evidence"}]
    validate_host_selection(resources)
    generated = {"id": "generated", "canonical_file": str(catalog.parent / "generated.png")}
    resources["selected_visual_references"] = [generated]
    with pytest.raises(SystemExit, match="authenticity_generated"):
        augment_profile_core_references(profile, resources, libraries)
    resources["selected_visual_references"] = [copy.deepcopy(result["candidates"][0])]
    items["good"]["provenance"]["generated_reference"] = True
    write(catalog, {"items": items})
    with pytest.raises(ValueError, match="authenticity_generated"):
        validate_host_selection(resources)


def test_both_cli_routes_and_existing_browse(library):
    root, _, config, intent, _, add, _ = library
    add("candidate")
    before = intent.read_bytes()
    for script in ("retrieve_references.py", "list_library.py"):
        result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts" / script), "--config", str(config),
                                 "--intent", str(intent), "--output", str(root / "cli.json"),
                                 "--sheet", str(root / "cli.png")], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["candidate_count"] == 1
    cfg = json.loads(config.read_text())
    cfg["library_sets"] = {"root": str(root), "records": {}, "selected": {}}
    write(config, cfg)
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/list_library.py"), "--config", str(config),
                             "--kind", "visual_references", "--query", "candidate"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["visual_references"][0]["id"] == "candidate"
    assert intent.read_bytes() == before


def test_catalog_lock_is_metadata_and_other_unregistered_files_still_fail(tmp_path):
    profiles = tmp_path / "profiles"
    catalog = profiles / "test/libraries/visual_references/catalog.json"
    write(profiles / "test/profile.json", {"profile_id": "test"})
    write(catalog, {"items": {}})
    catalog.with_suffix(".json.lock").touch()
    command = [sys.executable, str(ROOT / "slidepoise/scripts/preflight_catalogs.py"),
               "--profiles-root", str(profiles), "--profile", "test"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    (catalog.parent / "unexpected.png").touch()
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    assert "unregistered asset unexpected.png" in result.stdout
