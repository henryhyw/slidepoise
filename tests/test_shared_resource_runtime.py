"""Shared selections have the same effect in sessions, browsing and retrieval."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from framework import library_sets, profile_authoring, sessions
from framework.paths import BUNDLED_PROFILES_ROOT, data_home
from framework.profiles import initialize_home
from framework.storage import revision, write
from slidepoise.resource_catalogs import resolve_libraries, selected_records
from slidepoise.reference_retrieval import retrieve, validate_host_selection

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))
from prepare_generation import augment_selected_components


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(BUNDLED_PROFILES_ROOT)
    return data_home()


def reference(set_id, tmp_path, name):
    source = tmp_path / f"{name}.png"
    Image.new("RGB", (80, 45), "white").save(source)
    return library_sets.add_resource(set_id, source, name=name, description="parallel comparison options",
                                     source_type="user_private_document", source_page="1")


def choose(profile, selections, subsets=None):
    document = profile_authoring.profile_payload(profile)
    profile_authoring.update_profile(profile, {"library_sets": selections, "library_items": subsets or {}}, document["revision"])


def test_new_items_and_edits_flow_to_all_whole_set_profiles_but_not_subsets(home, tmp_path):
    set_id = library_sets.create_set("Team references", "visual_references")["id"]
    first = reference(set_id, tmp_path, "first")
    other = profile_authoring.create_profile("Client profile")["id"]
    choices = {"visual_references": [set_id], "icons": [], "components": []}
    choose("consulting", choices)
    choose(other, choices, {"visual_references": {set_id: [first["id"]]}})
    run = sessions.create("Current resources", profile="consulting")
    second = reference(set_id, tmp_path, "second")
    cfg = sessions.resolve(run)
    assert {item[2]["id"] for item in selected_records(cfg["libraries"]["visual_references"])} == {first["id"], second["id"]}
    assert [item["id"] for item in library_sets.selected_items(profile_authoring.profile_payload(other)["profile"], "visual_references")] == [first["id"]]
    choose("consulting", {**choices, "visual_references": []})
    assert sessions.resolve(run)["libraries"]["visual_references"]["sources"] == []
    assert [item["id"] for item in library_sets.selected_items(profile_authoring.profile_payload(other)["profile"], "visual_references")] == [first["id"]]
    assert not (home / "profiles" / other / "libraries").exists()


def test_selected_items_reach_both_cli_routes_and_retrieval_and_generation_guard(home, tmp_path):
    set_id = library_sets.create_set("Shared comparison", "visual_references")["id"]
    first, second = [reference(set_id, tmp_path, name) for name in ("first", "second")]
    choose("consulting", {"visual_references": [set_id], "icons": [], "components": []},
           {"visual_references": {set_id: [first["id"]]}})
    cfg = sessions.resolve(sessions.create("Subset", profile="consulting"))
    config_path = tmp_path / "config.json"
    write(config_path, cfg)
    script = ROOT / "slidepoise/scripts/list_library.py"
    for args in (("--profile", "consulting"), ("--config", str(config_path))):
        result = subprocess.run([sys.executable, str(script), "--kind", "visual_references", *args], capture_output=True, text=True, check=True)
        assert [item["resource_id"] for item in json.loads(result.stdout)["visual_references"]] == [first["resource_id"]]
    intent = tmp_path / "intent.json"
    write(intent, {"communication_job": "parallel comparison"})
    result = retrieve(config_path, intent, tmp_path / "candidates.json", tmp_path / "sheet.png")
    assert [item["resource_id"] for item in result["candidates"]] == [first["resource_id"]]
    selection = {"reference_retrieval": result["reference_retrieval"], "selected_visual_references": result["candidates"]}
    validate_host_selection(selection, cfg["libraries"]["visual_references"])
    selection["selected_visual_references"] = [{**second, "canonical_file": second["path"]}]
    with pytest.raises(ValueError, match="resolve uniquely"):
        validate_host_selection(selection)
    selection["selected_visual_references"] = result["candidates"]
    with pytest.raises(ValueError, match="resolve uniquely"):
        validate_host_selection(selection, {"sources": []})
    legacy = {**selection, "reference_retrieval": {key: value for key, value in selection["reference_retrieval"].items() if key != "sources"}}
    with pytest.raises(ValueError, match="resolve uniquely"):
        validate_host_selection(legacy, {"sources": []})
    choose("consulting", {"visual_references": [], "icons": [], "components": []})
    write(config_path, sessions.resolve(sessions.create("Empty", profile="consulting")))
    assert retrieve(config_path, intent, tmp_path / "empty.json", tmp_path / "empty.png")["candidates"] == []


def test_qualified_component_ids_disambiguate_shared_sets_and_respect_subsets(home):
    ids = [library_sets.create_set(name, "components")["id"] for name in ("One", "Two")]
    for set_id in ids:
        path, _ = library_sets.set_catalog(set_id)
        write(path, {"items": {"same": {"id": "same", "name": set_id, "grammar": {"purpose": "comparison"}}}})
    libraries, _ = resolve_libraries({"library_sets": {"components": ids}}, home / "library-sets")
    with pytest.raises(SystemExit, match="not in"):
        augment_selected_components({"selected_components": [{"id": "same", "reason": "compare"}]}, libraries=libraries)
    result = augment_selected_components({"selected_components": [{"resource_id": "two:same", "reason": "compare"}]}, libraries=libraries)
    assert result["selected_components"][0]["name"] == "two"
    libraries, _ = resolve_libraries({"library_sets": {"components": ids}, "library_items": {"components": {"two": []}}}, home / "library-sets")
    with pytest.raises(SystemExit, match="not in"):
        augment_selected_components({"selected_components": [{"resource_id": "two:same", "reason": "compare"}]}, libraries=libraries)
