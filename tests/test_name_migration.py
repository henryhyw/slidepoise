from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework import installer
from framework.migration import migrate_legacy_home
from framework.profiles import hash_file, initialize_home


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("SLIDEPOISE_HOME", raising=False)
    monkeypatch.delenv("SLIDECRAFT_HOME", raising=False)
    return tmp_path


def test_fresh_install_has_no_archive(isolated_home):
    source = isolated_home / "bundled"
    (source / "sample").mkdir(parents=True)
    (source / "sample" / "profile.json").write_text(json.dumps({"profile_id": "sample"}))
    assert migrate_legacy_home()["reason"] == "fresh_install"
    initialize_home(source)
    assert not (isolated_home / ".slidepoise" / "archive").exists()


def test_consulting_profile_id_upgrade_preserves_user_configuration(isolated_home):
    home = isolated_home / ".slidepoise"
    legacy = home / "profiles" / "pwc-consulting"
    (legacy / "libraries" / "visual_references").mkdir(parents=True)
    (legacy / "profile.json").write_text(json.dumps({
        "profile_id": "pwc-consulting",
        "name": "My consulting style",
        "custom_guidance": "Keep this exact instruction",
    }))
    (legacy / "libraries" / "visual_references" / "user-reference.png").write_bytes(b"user owned")
    (home / "settings.json").write_text(json.dumps({"active_profile": "pwc-consulting"}))
    (home / "config.json").write_text(json.dumps({
        "schema_version": "3.6.0",
        "user_design_overrides": {"pwc-consulting": {"style": {"body_font": "Custom Sans"}}},
        "library_locations": {"pwc-consulting": {"visual_references": "/custom/references"}},
        "design": {"profile": "pwc-consulting"},
    }))
    source = Path(__file__).resolve().parents[1] / "profiles"

    result = initialize_home(source)

    current = home / "profiles" / "consulting"
    assert not legacy.exists()
    assert json.loads((current / "profile.json").read_text())["custom_guidance"] == "Keep this exact instruction"
    assert (current / "libraries" / "visual_references" / "user-reference.png").read_bytes() == b"user owned"
    assert json.loads((home / "settings.json").read_text())["active_profile"] == "consulting"
    config = json.loads((home / "config.json").read_text())
    assert config["user_design_overrides"]["consulting"]["style"]["body_font"] == "Custom Sans"
    assert config["library_locations"]["consulting"]["visual_references"] == "/custom/references"
    assert config["design"]["profile"] == "consulting"
    assert result["files"]["profile_ids_migrated"] == 1
    assert (home / "archive" / "profile-id-migration" / "pwc-consulting" / "profile.json").is_file()


def test_consulting_profile_id_upgrade_refreshes_untouched_bundled_files(isolated_home):
    home = isolated_home / ".slidepoise"
    source = Path(__file__).resolve().parents[1] / "profiles"
    legacy = home / "profiles" / "pwc-consulting"
    legacy.mkdir(parents=True)
    profile = json.loads((source / "consulting" / "profile.json").read_text())
    profile["profile_id"] = "pwc-consulting"
    (legacy / "profile.json").write_text(json.dumps(profile))
    retired = legacy / "libraries" / "visual_references" / "retired-reference.png"
    retired.parent.mkdir(parents=True)
    retired.write_bytes(b"old bundled reference")
    retired_component = home / "library-sets" / "components" / "consulting-core" / "retired-component.png"
    retired_component.parent.mkdir(parents=True)
    retired_component.write_bytes(b"old bundled component")
    files = {
        "profiles/pwc-consulting/profile.json": hash_file(legacy / "profile.json"),
        "profiles/pwc-consulting/libraries/visual_references/retired-reference.png": hash_file(retired),
        "library-sets/components/consulting-core/retired-component.png": hash_file(retired_component),
    }
    (home / "manifest.json").write_text(json.dumps({"files": files}))
    (home / "settings.json").write_text(json.dumps({"active_profile": "pwc-consulting"}))

    initialize_home(source)

    current = home / "profiles" / "consulting"
    assert json.loads((current / "profile.json").read_text()) == json.loads((source / "consulting" / "profile.json").read_text())
    assert not (current / "libraries" / "visual_references" / "retired-reference.png").exists()
    assert next((home / "archive").glob("retired-bundle-*/consulting/libraries/visual_references/retired-reference.png")).read_bytes() == b"old bundled reference"
    assert not retired_component.exists()
    assert next((home / "archive").glob("retired-bundle-*/components/consulting-core/retired-component.png")).read_bytes() == b"old bundled component"


def test_migration_keeps_absolute_paths_and_evidence(isolated_home):
    legacy = isolated_home / ".slidecraft"
    (legacy / "workspace").mkdir(parents=True)
    evidence = legacy / "workspace" / "review.json"
    payload = json.dumps({"source": str(legacy / "profiles"), "sha256": "unchanged"}).encode()
    evidence.write_bytes(payload)
    result = migrate_legacy_home()
    assert result["migrated"] is True
    assert legacy.is_symlink()
    assert legacy.resolve() == isolated_home / ".slidepoise"
    assert evidence.read_bytes() == payload
    assert (isolated_home / ".slidepoise/workspace/review.json").read_bytes() == payload
    assert migrate_legacy_home()["reason"] == "already_migrated"


def test_migration_preserves_settings_and_backs_up_changed_config(isolated_home):
    legacy = isolated_home / ".slidecraft"
    legacy.mkdir()
    config = {
        "self_update": {"config_location": "$SLIDECRAFT_HOME/config.json"},
        "remote_sources": {"remix_icon": {"enabled": True}},
        "measurement": {"segmentation": {"mode": "never", "checkpoint": "/custom/model.pt"}},
    }
    original = json.dumps(config).encode()
    (legacy / "config.json").write_bytes(original)
    settings = b'{"active_profile":"personal-website"}'
    (legacy / "settings.json").write_bytes(settings)
    migrate_legacy_home()
    home = isolated_home / ".slidepoise"
    result = json.loads((home / "config.json").read_text())
    assert result["self_update"]["config_location"] == "$SLIDEPOISE_HOME/config.json"
    assert result["remote_sources"] == config["remote_sources"]
    assert result["measurement"] == config["measurement"]
    assert (home / "settings.json").read_bytes() == settings
    backup = home / "archive/name-migration/config.json"
    assert backup.read_bytes() == original
    migrate_legacy_home()
    assert backup.read_bytes() == original


def test_migration_never_merges_existing_homes(isolated_home):
    for name in (".slidecraft", ".slidepoise"):
        folder = isolated_home / name
        folder.mkdir()
        (folder / "sentinel").write_text(name)
    with pytest.raises(RuntimeError, match="Cannot safely migrate"):
        migrate_legacy_home()
    for name in (".slidecraft", ".slidepoise"):
        assert (isolated_home / name / "sentinel").read_text() == name


def test_explicit_home_does_not_move_legacy(isolated_home, monkeypatch):
    legacy = isolated_home / ".slidecraft"
    legacy.mkdir()
    monkeypatch.setenv("SLIDEPOISE_HOME", str(isolated_home / "custom"))
    assert migrate_legacy_home()["reason"] == "explicit_home"
    assert not legacy.is_symlink()
    assert not (isolated_home / ".slidepoise").exists()


def test_legacy_env_requires_explicit_change(isolated_home, monkeypatch):
    monkeypatch.setenv("SLIDECRAFT_HOME", str(isolated_home / "custom"))
    with pytest.raises(RuntimeError, match="SLIDEPOISE_HOME"):
        migrate_legacy_home()


def test_migration_rolls_back_if_alias_cannot_be_created(isolated_home, monkeypatch):
    legacy = isolated_home / ".slidecraft"
    legacy.mkdir()
    (legacy / "config.json").write_text("{}")
    def fail_link(*args, **kwargs):
        raise OSError("symlink unavailable")
    monkeypatch.setattr(Path, "symlink_to", fail_link)
    with pytest.raises(OSError, match="symlink unavailable"):
        migrate_legacy_home()
    assert (legacy / "config.json").read_text() == "{}"
    assert not (isolated_home / ".slidepoise").exists()


def test_skill_update_archives_once_and_removes_legacy_entry(isolated_home, monkeypatch):
    source = isolated_home / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("SlidePoise")
    monkeypatch.setattr(installer, "SKILL_ROOT", source)
    target = Path(installer.install_codex_skill())
    archive = isolated_home / ".slidepoise" / "archive"
    assert target.name == "slidepoise"
    assert not archive.exists()
    installer.install_codex_skill()
    assert not archive.exists()
    legacy = target.with_name("slidecraft")
    legacy.mkdir()
    (legacy / "SKILL.md").write_text("old user content")
    (source / "SKILL.md").write_text("SlidePoise updated")
    installer.install_codex_skill()
    assert not legacy.exists()
    backups = sorted(archive.iterdir())
    assert len(backups) == 2
    assert (next(archive.glob("legacy-skill-*")) / "SKILL.md").read_text() == "old user content"
    installer.install_codex_skill()
    assert sorted(archive.iterdir()) == backups
