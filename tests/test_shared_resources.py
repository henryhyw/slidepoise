"""Shared resource selection, imports and migration preserve user choices."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework import library_sets, profile_authoring
from framework.profiles import initialize_home
from framework.shared_resource_migration import migrate_shared_resources
from framework.storage import read, write


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("SLIDEPOISE_HOME", str(home))
    write(home / "library-sets/catalog.json", {"items": {}})
    write(home / "profiles/base/profile.json", {
        "profile_id": "base", "name": "Base", "purpose": "Shared resources",
        "design_overrides": {"style": {"body_font": "Arial"}},
        "library_sets": {"visual_references": [], "icons": [], "components": []},
    })
    return home


def add_image(home, set_id, name):
    path = home / f"{name}.png"
    path.write_bytes(name.encode())
    return library_sets.add_resource(set_id, path, name=name, source_type="user_private_document")


def test_shared_selection_reads_live_items_and_preserves_qualified_identity(home):
    first = library_sets.create_set("First references", "visual_references")
    second = library_sets.create_set("Second references", "visual_references")
    a = add_image(home, first["id"], "one")
    b = add_image(home, first["id"], "two")
    second_path, _ = library_sets.set_catalog(second["id"])
    write(second_path, {"items": {a["id"]: {"id": a["id"], "path": "other.png"}}})
    profile = {"library_sets": {"visual_references": [first["id"], second["id"]]}}
    library_sets.validate_selection(profile)
    items = library_sets.selected_items(profile, "visual_references")
    assert len(items) == 3
    assert len({item["resource_id"] for item in items}) == 3
    add_image(home, first["id"], "three")
    assert len(library_sets.selected_items(profile, "visual_references")) == 4
    profile["library_items"] = {"visual_references": {first["id"]: [b["id"]], second["id"]: []}}
    library_sets.validate_selection(profile)
    assert [item["resource_id"] for item in library_sets.selected_items(profile, "visual_references")] == [b["resource_id"]]


@pytest.mark.parametrize("sets,items", [
    ({"icons": ["references"]}, {}),
    ({"visual_references": ["missing"]}, {}),
    ({"visual_references": ["references", "references"]}, {}),
    ({"visual_references": ["references"]}, {"visual_references": {"references": ["missing"]}}),
    ({"visual_references": []}, {"visual_references": {"references": []}}),
    ({"visual_references": ["references"]}, {"visual_references": {"references": "all"}}),
])
def test_invalid_set_and_item_selections_are_rejected(home, sets, items):
    library_sets.create_set("References", "visual_references")
    with pytest.raises(ValueError):
        library_sets.validate_selection({"library_sets": sets, "library_items": items})


def test_profile_clone_reuses_selection_without_copying_assets(home):
    family = library_sets.create_set("References", "visual_references")
    added = add_image(home, family["id"], "sample")
    before = profile_authoring.profile_payload("base")
    selections = {"visual_references": [family["id"]], "icons": [], "components": []}
    subsets = {"visual_references": {family["id"]: [added["id"]]}}
    profile_authoring.update_profile("base", {"library_sets": selections, "library_items": subsets}, before["revision"])
    private = home / "profiles/base/source-documents/private.pptx"
    private.parent.mkdir()
    private.write_bytes(b"Never clone private source material")
    created = profile_authoring.create_profile("New style", based_on="base")
    assert created["profile"]["library_sets"] == selections
    assert created["profile"]["library_items"] == subsets
    assert [path.name for path in Path(created["root"]).iterdir()] == ["profile.json"]
    assert library_sets.selected_items(created["profile"], "visual_references")[0]["path"] == added["path"]


def test_legacy_add_resource_registers_shared_asset_and_updates_subset(home):
    family = library_sets.create_set("References", "visual_references")
    before = profile_authoring.profile_payload("base")
    profile_authoring.update_profile("base", {
        "library_sets": {"visual_references": [family["id"]]},
        "library_items": {"visual_references": {family["id"]: []}},
    }, before["revision"])
    image = home / "new.png"
    image.write_bytes(b"reference")
    added = profile_authoring.add_resource("base", "visual_references", image, name="New reference",
                                            description="Source composition", source_type="user_private_document", source_page="7")
    profile = profile_authoring.profile_payload("base")["profile"]
    assert profile["library_items"]["visual_references"][family["id"]] == [added["id"]]
    assert Path(added["path"]).is_relative_to(home / "library-sets")
    assert not (home / "profiles/base/libraries").exists()
    item = library_sets.selected_items(profile, "visual_references")[0]
    assert item["provenance"]["source_page"] == "7"
    assert item["provenance"]["generated_reference"] is False


def test_migration_deduplicates_custom_paths_and_symlinks_and_is_idempotent(home, tmp_path):
    external = tmp_path / "private-references"
    external.mkdir()
    (external / "same.png").write_bytes(b"preview")
    document = tmp_path / "source.pptx"
    document.write_bytes(b"private source")
    original = {"id": "existing-id", "name": "Existing", "path": "same.png", "preview_path": "same.png",
                "source_document_path": "../source.pptx", "custom_metadata": {"keep": ["unchanged"]},
                "provenance": {"source_type": "user_private_document", "source_page": 4}}
    write(external / "catalog.json", {"items": {"existing-id": original}})
    for identifier in ("base", "other"):
        folder = home / "profiles" / identifier
        write(folder / "profile.json", {"profile_id": identifier, "name": identifier,
              "visual_reference_priorities": {"core": ["existing-id"]}, "library_sets": {"icons": []}})
        (folder / "libraries").mkdir()
        (folder / "libraries/visual_references").symlink_to(external, target_is_directory=True)
    config = {"library_locations": {"base": {"visual_references": str(external)}}}
    write(home / "config.json", config)
    migrated = migrate_shared_resources(home)
    assert migrated["sets"] == 1
    assert migrated["profiles"] == 2
    assert read(Path(migrated["backup"]) / "config.json") == config
    first = profile_authoring.profile_payload("base")["profile"]
    second = profile_authoring.profile_payload("other")["profile"]
    assert first["library_sets"] == second["library_sets"]
    selected = library_sets.selected_items(first, "visual_references")[0]
    assert selected["id"] == "existing-id"
    assert Path(selected["path"]).read_bytes() == b"preview"
    assert Path(selected["source_document_path"]).read_bytes() == b"private source"
    assert Path(selected["source_document_path"]).is_relative_to(home / "library-sets")
    assert selected["custom_metadata"] == original["custom_metadata"]
    assert first["visual_reference_priorities"]["core"] == [selected["resource_id"]]
    assert read(home / "config.json")["library_locations"] == {}
    assert read(external / "catalog.json")["items"]["existing-id"] == original
    before = {p: p.read_bytes() for p in home.rglob("*.json")}
    assert migrate_shared_resources(home)["migrated"] is False
    assert {p: p.read_bytes() for p in home.rglob("*.json")} == before


def test_setup_migrates_before_retiring_old_bundle_files(home, tmp_path):
    profile_root = home / "profiles/base"
    profile = read(profile_root / "profile.json")
    profile["library_sets"].pop("visual_references")
    write(profile_root / "profile.json", profile)
    refs = profile_root / "libraries/visual_references"
    refs.mkdir(parents=True)
    (refs / "old.png").write_bytes(b"keep this reference")
    write(refs / "catalog.json", {"items": {"old": {"id": "old", "path": "old.png"}}})
    from framework.profiles import hash_file
    write(home / "manifest.json", {"files": {f"profiles/base/libraries/visual_references/{name}": hash_file(refs / name)
                                             for name in ("catalog.json", "old.png")}})
    source = tmp_path / "new-profiles"
    write(source / "base/profile.json", {"profile_id": "base", "library_sets": {"visual_references": []}})
    initialize_home(source)
    updated = profile_authoring.profile_payload("base")["profile"]
    assert Path(library_sets.selected_items(updated, "visual_references")[0]["path"]).read_bytes() == b"keep this reference"
    assert (refs / "old.png").read_bytes() == b"keep this reference"
    assert (refs / "catalog.json").is_file()
    assert initialize_home(source)["shared_resources"]["migrated"] is False


def test_catalog_key_does_not_replace_stable_item_identity(home):
    family = library_sets.create_set("References", "visual_references")
    path, _ = library_sets.set_catalog(family["id"])
    write(path, {"items": {"asset.png": {"id": "stable-id", "path": "asset.png"}}})
    profile = {"library_sets": {"visual_references": [family["id"]]},
               "library_items": {"visual_references": {family["id"]: ["stable-id"]}}}
    library_sets.validate_selection(profile)
    selected = library_sets.selected_items(profile, "visual_references")
    assert selected[0]["id"] == "stable-id"
    assert selected[0]["resource_id"] == "references:stable-id"


def test_mutation_before_setup_never_writes_into_bundle(tmp_path, monkeypatch):
    home = tmp_path / "fresh-home"
    bundle = tmp_path / "bundle"
    monkeypatch.setenv("SLIDEPOISE_HOME", str(home))
    monkeypatch.setattr(library_sets, "BUNDLED_LIBRARY_SETS_ROOT", bundle)
    write(bundle / "catalog.json", {"items": {}})
    before = (bundle / "catalog.json").read_bytes()
    created = library_sets.create_set("Personal references", "visual_references")
    assert Path(created["root"]).is_relative_to(home)
    assert (bundle / "catalog.json").read_bytes() == before
    assert list(bundle.iterdir()) == [bundle / "catalog.json"]
