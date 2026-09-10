from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from framework import design, sessions, profile_authoring, library_sets, components, run_events
from framework.paths import BUNDLED_PROFILES_ROOT, data_home
from framework.profiles import initialize_home
from framework.storage import read, revision, write
from webapp import panel, server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))
from prepare_generation import augment_selected_components
from make_asset_contact_sheet import collect_resource_review_items


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(BUNDLED_PROFILES_ROOT)
    monkeypatch.setattr(server, "REGISTRY", data_home() / "workspace/runs.json")
    return data_home()


@pytest.fixture
def run(home):
    return sessions.create("Integration probe")


def test_settings_change_reaches_panel_and_agent_once(run):
    before = panel.snapshot(run)["revision"]
    values = read(run / "session-overrides.json")
    values["design_overrides"] = {"style": {"body_font": "Courier New"}}
    sessions.save_overrides(run, values, revision(run / "session-overrides.json"))
    assert panel.snapshot(run)["revision"] != before
    assert server.run_detail(run)["values"]["body_font"] == "Courier New"
    assert len(run_events.pending(run)["events"]) == 1


def test_direct_agent_file_edit_refreshes_panel(run):
    before = panel.snapshot(run)["revision"]
    write(run / "session-overrides.json", {"profile": "monochrome-modern"})
    assert panel.snapshot(run)["revision"] != before


def test_metadata_and_adopted_defaults_notify_agent(run):
    sessions.patchmetadata(run, {"requirements": "Keep this short"}, revision(run / "session.json"))
    sessions.adopt_defaults(run, revision(run / "work/session-defaults.json"))
    assert [e["kind"] for e in run_events.pending(run)["events"]] == ["requirements_changed", "defaults_updated"]


def test_console_revision_observes_direct_profile_and_component_edits(home):
    before = server.console_revision()
    profile = home / "profiles/editorial-archive/profile.json"
    write(profile, {**read(profile), "purpose": "Updated externally"})
    assert server.console_revision() != before
    before = server.console_revision()
    catalog = home / "library-sets/components/editorial-core/catalog.json"
    write(catalog, {**read(catalog), "description": "Edited directly"})
    assert server.console_revision() != before


def test_profile_clone_copies_effective_style_and_is_independent(home):
    design.save_defaults("editorial-archive", {"body_font": "Courier New", "primary": "#123456"}, revision(home / "config.json"))
    created = profile_authoring.create_profile("My style", based_on="editorial-archive")
    cloned = design.presentation_values(design.resolve_default(created["id"]))
    assert cloned["body_font"] == "Courier New" and cloned["primary"] == "#123456"
    design.save_defaults("editorial-archive", {"body_font": "Georgia"}, revision(home / "config.json"))
    assert design.resolve_default(created["id"])["design"]["style"]["body_font"] == "Courier New"


def test_clone_captures_custom_reference_location(home, tmp_path):
    custom = tmp_path / "references"
    write(custom / "catalog.json", {"items": {"custom": {"id": "custom", "path": "image.png"}}})
    (custom / "image.png").write_bytes(b"reference fixture")
    cfg = read(home / "config.json")
    cfg["library_locations"] = {"editorial-archive": {"visual_references": str(custom)}}
    write(home / "config.json", cfg)
    clone = profile_authoring.create_profile("Custom references", based_on="editorial-archive")
    copied = Path(clone["root"]) / "libraries/visual_references"
    assert read(copied / "catalog.json")["items"]["custom"]["id"] == "custom"
    assert (copied / "image.png").read_bytes() == b"reference fixture"


def test_library_listing_uses_session_sets_and_custom_reference_location(run, tmp_path):
    cfg = sessions.resolve(run)
    cfg["library_sets"]["selected"] = {"icons": [], "components": []}
    custom = tmp_path / "custom.json"
    write(custom, {"items": {"only": {"id": "only", "name": "Only selected reference"}}})
    cfg["libraries"]["visual_references"]["catalog"] = str(custom)
    resolved = tmp_path / "resolved.json"
    write(resolved, cfg)
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/list_library.py"), "--config", str(resolved)], capture_output=True, text=True, check=True)
    listed = json.loads(result.stdout)
    assert listed["icons"] == [] and listed["components"] == []
    assert [r["id"] for r in listed["visual_references"]] == ["only"]


def test_imported_native_component_has_usable_generation_preview(home, tmp_path, monkeypatch):
    family = library_sets.create_set("Custom components", "components")
    source = home / "library-sets/components/consulting-core/consulting-native-components.pptx"
    imported = library_sets.add_resource(family["id"], source, name="Editable component")
    assert components.inspect(family["id"], imported["id"])["native"]
    catalog, entries = library_sets.set_catalog(family["id"])
    assert entries["items"][imported["id"]]["native_source_slide_number"] == 1
    # Test the real handoff, with only the external renderer replaced by a fixture.
    import component_preview
    calls = []
    from PIL import Image
    def render(command, **_):
        calls.append(command)
        Image.new("RGB", (160, 90), "white").save(command[command.index("--output") + 1])
        return subprocess.CompletedProcess(command, 0, "", "")
    monkeypatch.setattr(component_preview.subprocess, "run", render)
    selection = {"selected_components": [{"component_id": imported["id"], "reason": "Supports this comparison"}]}
    libraries = {"components": {"catalogs": [str(catalog)]}}
    resolved = augment_selected_components(selection, libraries=libraries)
    component = resolved["selected_components"][0]
    assert Path(component["preview_file"]).is_file()
    assert Path(component["canonical_file"]).suffix == ".pptx"
    assert collect_resource_review_items(resolved)
    augment_selected_components(selection, libraries=libraries)
    assert len(calls) == 1
    Path(component["canonical_file"]).touch()
    augment_selected_components(selection, libraries=libraries)
    assert len(calls) == 1  # Hash binding avoids needless rendering after a timestamp-only change.
    with Path(component["canonical_file"]).open("ab") as file:
        file.write(b"changed fixture")
    augment_selected_components(selection, libraries=libraries)
    assert len(calls) == 2


def test_session_panel_snapshot_only_exposes_settings_assets_and_events(run):
    upload = run / "uploads/reference.png"
    upload.write_bytes(b"image")
    view = panel.snapshot(run)
    assert set(view) == {"path", "materials", "pending_events", "settings_revisions", "revision"}
    assert view["materials"][0]["name"] == "reference.png"
    for removed in ("stages", "downloads", "versions", "activity", "approvals", "developer"):
        assert removed not in view


def test_npm_entry_keeps_callers_working_directory(home, tmp_path):
    result = subprocess.run(["node", str(ROOT / "bin/slidepoise.js"), "run", "create", "Relative", "--location", "presentation"],
                            cwd=tmp_path, env={**os.environ, "PYTHON": sys.executable}, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["path"] == str((tmp_path / "presentation").resolve())
