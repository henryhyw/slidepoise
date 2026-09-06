from __future__ import annotations

import json

import pytest

from framework import design, library_sets, profile_authoring, sessions
from framework.paths import BUNDLED_PROFILES_ROOT, DEFAULT_CONFIG, data_home
from framework.profiles import initialize_home, active_profile_id, set_active_profile
from framework.storage import ConflictError, revision, write


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(BUNDLED_PROFILES_ROOT)
    write(data_home() / "config.json", json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8")))
    return data_home()


def test_runs_capture_defaults_and_remain_isolated(home):
    first = sessions.create("First")
    original = sessions.resolve(first)["design"]["style"]["display_font"]
    defaults = design.defaults_payload()
    design.save_defaults(defaults["values"]["profile"], {"display_font": "Courier New"}, defaults["revision"])
    second = sessions.create("Second")
    assert sessions.resolve(first)["design"]["style"]["display_font"] == original
    assert sessions.resolve(second)["design"]["style"]["display_font"] == "Courier New"
    overrides = json.loads((first / "session-overrides.json").read_text(encoding="utf-8"))
    overrides["density"] = "spacious"
    sessions.save_overrides(first, overrides, revision(first / "session-overrides.json"))
    assert sessions.resolve(first)["design"]["style"]["density"] == "spacious"
    assert sessions.resolve(second)["design"]["style"]["density"] != "spacious"


def test_default_profile_selection_is_shared_and_preserves_existing_runs(home):
    original = active_profile_id()
    first = sessions.create("Existing presentation")
    profile_path = home / "profiles/personal-monochrome/profile.json"
    before = profile_path.read_bytes()
    set_active_profile("personal-monochrome")
    assert design.defaults_payload(original)["active_profile"] == "personal-monochrome"
    assert design.defaults_payload()["values"]["profile"] == "personal-monochrome"
    assert sessions.resolve(first)["design"]["profile"] == original
    assert sessions.resolve(sessions.create("New presentation"))["design"]["profile"] == "personal-monochrome"
    assert profile_path.read_bytes() == before
    with pytest.raises(FileNotFoundError):
        set_active_profile("missing-profile")
    assert active_profile_id() == "personal-monochrome"


def test_concurrent_session_update_requires_current_revision(home):
    root = sessions.create("Concurrent")
    path = root / "session-overrides.json"
    old = revision(path)
    sessions.save_overrides(root, {"profile": "consulting", "density": "spacious"}, old)
    with pytest.raises(ConflictError, match="another window or Agent"):
        sessions.save_overrides(root, {"profile": "personal-website"}, old)


def test_agent_can_create_profile_and_add_reference(home, tmp_path):
    profile = profile_authoring.create_profile("Studio Notes")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"visual-reference")
    result = profile_authoring.add_resource(profile["id"], "visual_references", reference,
                                             name="Editorial rhythm", description="Asymmetric type and image rhythm")
    assert result["profile"] == "studio-notes"
    assert (home / "profiles/studio-notes/libraries/visual_references" / result["path"].split("/")[-1]).is_file()


def test_profile_selects_shared_sets_and_run_can_override_them(home):
    profile = design.defaults_payload("consulting")
    assert profile["selected_sets"]["components"] == ["consulting-core"]
    root = sessions.create("Set override", profile="consulting")
    overrides = json.loads((root / "session-overrides.json").read_text())
    overrides["library_sets"] = {"icons": ["remix-icon"], "components": ["editorial-core"]}
    sessions.save_overrides(root, overrides, revision(root / "session-overrides.json"))
    resolved = sessions.resolve(root)
    assert resolved["library_sets"]["selected"] == overrides["library_sets"]
    assert resolved["remote_sources"]["remix_icon"]["enabled"] is True
    assert resolved["remote_sources"]["wikimedia_commons"]["enabled"] is False


def test_agent_can_create_and_fill_shared_library_set(home, tmp_path):
    created = library_sets.create_set("Research symbols", "icons", "A coherent set for research slides")
    icon = tmp_path / "research.svg"
    icon.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    added = library_sets.add_resource(created["id"], icon, name="Research", license_name="CC0")
    assert added["set_id"] == "research-symbols"
    assert library_sets.set_catalog("research-symbols")[1]["items"][added["id"]]["name"] == "Research"
