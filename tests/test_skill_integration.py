from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from webapp import server
from framework.profiles import initialize_home, migrate_config

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "slidepoise"
FRAMEWORK = ROOT / "framework"
PROFILES = ROOT / "profiles"
sys.path.insert(0, str(SKILL / "scripts"))

from prepare_generation import augment_selected_components, build_brief, build_contract, build_style_context
from make_asset_contact_sheet import build_contact_sheet
from slidepoise_runtime import resolve_scene_paths


def run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / name), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def generic_generation_inputs(tmp_path: Path) -> tuple[dict, dict, dict]:
    session = tmp_path / "session.json"
    resolved = tmp_path / "resolved.json"
    session.write_text(json.dumps({"profile": "monochrome-modern"}), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base", str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
        "--profiles-root", str(PROFILES),
        "--session", str(session),
        "--output", str(resolved),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    config = json.loads(resolved.read_text(encoding="utf-8"))
    intent = json.loads((SKILL / "schemas" / "slide-intent.example.json").read_text(encoding="utf-8"))
    intent["user_required_assets"] = []
    resources = {
        "style_context": build_style_context(config),
        "style_direction": {"intent": "Use the selected profile to communicate the approved information plan."},
        "selected_visual_references": [],
        "selected_assets": [],
        "selected_components": [],
    }
    return config, intent, resources


def test_framework_and_profiles_validate() -> None:
    config = run_script("preflight_config.py", str(FRAMEWORK / "defaults" / "slidepoise-config.json"))
    catalogs = run_script("preflight_catalogs.py", "--profiles-root", str(PROFILES))
    assert config.returncode == 0, config.stderr or config.stdout
    assert catalogs.returncode == 0, catalogs.stderr or catalogs.stdout


def test_profile_catalog_rejects_unregistered_assets(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    shutil.copytree(PROFILES / "consulting", profiles / "consulting")
    extra = profiles / "consulting" / "libraries" / "visual_references" / "unregistered.png"
    extra.write_bytes(b"unregistered")
    result = run_script(
        "preflight_catalogs.py",
        "--profiles-root",
        str(profiles),
        "--library-sets-root",
        str(ROOT / "library-sets"),
    )
    assert result.returncode == 2
    assert "unregistered asset unregistered.png" in result.stdout


def test_segmentation_override_resolves(tmp_path: Path) -> None:
    session = json.loads((FRAMEWORK / "templates" / "session-overrides-template.json").read_text(encoding="utf-8"))
    session["measurement"] = {"segmentation": {"mode": "auto"}}
    session_path = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    session_path.write_text(json.dumps(session), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base",
        str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
        "--profiles-root",
        str(PROFILES),
        "--session",
        str(session_path),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["measurement"]["segmentation"]["mode"] == "auto"


@pytest.mark.parametrize("profile_id", ["editorial-archive", "monochrome-modern"])
def test_profile_owned_visual_tokens_do_not_leak_from_base(profile_id: str, tmp_path: Path) -> None:
    session = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    session.write_text(json.dumps({"profile": profile_id}), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base", str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
        "--profiles-root", str(PROFILES),
        "--session", str(session),
        "--output", str(output),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    resolved = json.loads(output.read_text(encoding="utf-8"))
    expected = json.loads((PROFILES / profile_id / "profile.json").read_text(encoding="utf-8"))["design_overrides"]["semantic_style_tokens"]
    assert resolved["design"]["semantic_style_tokens"] == expected
    assert resolved["design"]["style"]["density"] == "balanced"


def test_partial_user_token_override_preserves_the_profile_vocabulary(tmp_path: Path) -> None:
    base = json.loads((FRAMEWORK / "defaults" / "slidepoise-config.json").read_text(encoding="utf-8"))
    base["user_design_overrides"] = {
        "editorial-archive": {
            "semantic_style_tokens": {"primary_text": {"color": "#123456"}}
        }
    }
    base_path = tmp_path / "base.json"
    session_path = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    base_path.write_text(json.dumps(base), encoding="utf-8")
    session_path.write_text(json.dumps({"profile": "editorial-archive"}), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base", str(base_path),
        "--profiles-root", str(PROFILES),
        "--session", str(session_path),
        "--output", str(output),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    tokens = json.loads(output.read_text(encoding="utf-8"))["design"]["semantic_style_tokens"]
    assert tokens["primary_text"]["color"] == "#123456"
    assert tokens["archive_paper"]["fill"] == "#F1ECE2"
    assert "symbol_surface" not in tokens


def test_remote_source_overrides_resolve_independently(tmp_path: Path) -> None:
    session = json.loads((FRAMEWORK / "templates" / "session-overrides-template.json").read_text(encoding="utf-8"))
    session["remote_sources"]["remix_icon"]["enabled"] = True
    session["remote_sources"]["wikimedia_commons"]["enabled"] = True
    session_path = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    session_path.write_text(json.dumps(session), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base",
        str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
        "--profiles-root",
        str(PROFILES),
        "--session",
        str(session_path),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    sources = json.loads(output.read_text(encoding="utf-8"))["remote_sources"]
    assert sources["remix_icon"]["enabled"] is True
    assert sources["wikimedia_commons"]["enabled"] is True


@pytest.mark.parametrize("remix", [None, True, False])
@pytest.mark.parametrize("commons", [None, True, False])
def test_profile_switch_preserves_framework_and_run_source_settings(tmp_path: Path, remix, commons) -> None:
    base = json.loads((FRAMEWORK / "defaults" / "slidepoise-config.json").read_text())
    base["remote_sources"]["remix_icon"]["enabled"] = True
    base["remote_sources"]["wikimedia_commons"]["enabled"] = False
    base_path = tmp_path / "base.json"
    base_path.write_text(json.dumps(base))
    session_path = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    source_snapshots = []
    for profile in ("consulting", "editorial-archive"):
        session_path.write_text(json.dumps({
            "profile": profile,
            "remote_sources": {
                "remix_icon": {"enabled": remix},
                "wikimedia_commons": {"enabled": commons},
            },
        }))
        result = run_script("resolve_config.py", "--base", str(base_path),
                            "--profiles-root", str(PROFILES), "--session", str(session_path),
                            "--output", str(output))
        assert result.returncode == 0, result.stderr
        resolved = json.loads(output.read_text())
        assert resolved["design"]["profile"] == profile
        sources = resolved["remote_sources"]
        assert sources["remix_icon"]["enabled"] is (True if remix is None else remix)
        assert sources["wikimedia_commons"]["enabled"] is (True if commons is None else commons)
        source_snapshots.append(sources)
    assert source_snapshots[0] == source_snapshots[1]


@pytest.mark.parametrize("enabled", ["false", "true", 0, 1, [], {}])
def test_remote_switch_rejects_non_boolean_values(tmp_path: Path, enabled) -> None:
    session = tmp_path / "session.json"
    output = tmp_path / "resolved.json"
    session.write_text(json.dumps({"remote_sources": {"remix_icon": {"enabled": enabled}}}))
    result = run_script("resolve_config.py", "--base", str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
                        "--profiles-root", str(PROFILES), "--session", str(session), "--output", str(output))
    assert result.returncode != 0
    assert "must be boolean or null" in result.stderr
    assert not output.exists()


def test_conflicting_legacy_source_override_cannot_reenable_disabled_source(tmp_path: Path) -> None:
    session = tmp_path / "session.json"
    session.write_text(json.dumps({
        "remote_sources": {"remix_icon": {"enabled": False}},
        "external_icon_fetch": {"enabled": True},
    }))
    result = run_script("resolve_config.py", "--base", str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
                        "--profiles-root", str(PROFILES), "--session", str(session),
                        "--output", str(tmp_path / "resolved.json"))
    assert result.returncode != 0
    assert "disagree" in result.stderr


def test_profile_component_resolution_uses_shared_set_catalog() -> None:
    libraries = {
        "components": {
            "catalog": str(ROOT / "library-sets" / "components" / "editorial-core" / "catalog.json")
        }
    }
    result = augment_selected_components(
        {"selected_components": [{"component_id": "personal-sharp-editorial-sequence", "reason": "Useful progression grammar."}]},
        "editorial-archive",
        libraries,
    )
    selected = result["selected_components"][0]
    assert selected["resource_form"] == "grammar_only"
    assert selected["source"] == "selected_shared_component_set"


def test_generation_handoff_preserves_the_complete_information_plan(tmp_path: Path) -> None:
    config, intent, resources = generic_generation_inputs(tmp_path)
    contract = build_contract(config, intent, resources)
    assert contract["communication_intent"] == intent
    assert contract["communication_intent"]["information_structure"]["type"] == intent["information_structure"]["type"]
    assert contract["resources"]["style_context"] == build_style_context(config)
    assert contract["user_language"]["reader_first"] is True
    assert contract["user_language"]["new_copy_em_dash"] == "avoid"
    brief = build_brief(contract)
    assert "USER-FACING LANGUAGE" in brief
    assert "Do not use an em dash in newly authored copy" in brief
    assert "continue without per-slide approval" not in brief
    assert "wait for explicit approval" not in brief




def test_changed_style_invalidates_the_combined_style_asset_context(tmp_path: Path) -> None:
    config, intent, resources = generic_generation_inputs(tmp_path)
    config["design"]["style"]["body_font"] = "Aptos"
    with pytest.raises(SystemExit, match="Style changed"):
        build_contract(config, intent, resources)


def test_style_only_context_sheet_remains_a_reviewable_artifact(tmp_path: Path) -> None:
    config, _intent, _resources = generic_generation_inputs(tmp_path)
    output = tmp_path / "style-assets.png"
    result = build_contact_sheet([], output, style_context=build_style_context(config),
                                 style_direction={"intent": "Quiet technical explanation"})
    assert output.is_file()
    assert result["asset_count"] == 0
    assert result["includes_style_context"] is True


def test_config_evidence_does_not_issue_stage_verdict() -> None:
    result = run_script("preflight_config.py", str(FRAMEWORK / "defaults" / "slidepoise-config.json"))
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["blocking_facts"] == []
    assert "mechanically_valid" not in payload
    assert "passed" not in payload


def test_config_evidence_reports_a_selected_remote_icon_set_disabled_by_the_session(tmp_path: Path) -> None:
    session = tmp_path / "session.json"
    resolved = tmp_path / "resolved.json"
    session.write_text(json.dumps({
        "profile": "consulting",
        "remote_sources": {"remix_icon": {"enabled": False}},
    }), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base", str(FRAMEWORK / "defaults" / "slidepoise-config.json"),
        "--profiles-root", str(PROFILES),
        "--session", str(session),
        "--output", str(resolved),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    evidence = run_script("preflight_config.py", str(resolved))
    payload = json.loads(evidence.stdout)
    assert evidence.returncode == 0
    assert payload["blocking_facts"] == []
    assert payload["configuration_facts"] == [
        "selected remote icon Library Set is disabled for this run: remix-icon (remix_icon)"
    ]


def test_sam_auto_falls_back_without_checkpoint() -> None:
    sys.path.insert(0, str(SKILL / "runtime" / "scripts"))
    import numpy as np
    from sam_optional import attempt

    config = json.loads((FRAMEWORK / "defaults" / "slidepoise-config.json").read_text(encoding="utf-8"))
    entities = [{
        "id": "irregular-a",
        "kind": "novel_visual",
        "bbox_hint": [1, 1, 4, 4],
        "segmentation_role": "irregular_filled_boundary",
        "segmentation_preference": "sam_if_available",
    }]
    results, report = attempt(np.zeros((8, 8, 3), dtype=np.uint8), entities, config, mode_override="auto")
    assert results == {}
    assert report["skip_reason"] == "checkpoint_not_configured"
    assert report["eligible_entity_ids"] == ["irregular-a"]


def test_console_separates_profile_references_from_shared_library_sets(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(PROFILES)
    assert server.library("visual_references", "consulting")["count"] == 2
    assert server.library("visual_references", "editorial-archive")["count"] == 2
    assert server.library("visual_references", "monochrome-modern")["count"] == 2
    assert {item["id"] for item in server.library_sets.list_sets()} == {
        "remix-icon", "wikimedia-identity", "consulting-core", "editorial-core"
    }
    assert server.library_set("consulting-core")["count"] == 13


def test_run_creation_initializes_a_live_deck_outline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(server, "REGISTRY", tmp_path / "registry.json")
    run = server.create_run("Example", str(tmp_path / "example"))
    root = Path(run["path"])
    assert (root / "session-overrides.json").is_file()
    outline = json.loads((root / "work" / "deck-outline.json").read_text())
    assert outline["title"] == "Example"
    assert outline["slides"] == []
    assert (root / "slides").is_dir()
    assert not (root / "work" / "human-approvals.json").exists()


def test_render_deck_assembles_scenes_in_manifest_order(tmp_path: Path) -> None:
    scene = json.loads((ROOT / "tests" / "fixtures" / "continuous_connector_scene.json").read_text())["slide"]
    scene["slide_id"] = "first"
    scene["objects"][0]["id"] = "first-page-connector"
    scene["compiler_report"] = {
        "measurement": {"engine": "OpenCV", "opencv": "test"},
        "input_bindings": {
            "measured_scene_sha256": "test-measured",
            "reconstruction_contract_sha256": "test-contract",
            "resolved_design_sha256": "test-design",
        },
    }
    first = tmp_path / "first.json"
    first.write_text(json.dumps(scene))
    second_scene = json.loads(json.dumps(scene))
    second_scene["slide_id"] = "second"
    second_scene["objects"][0]["id"] = "second-page-connector"
    second = tmp_path / "second.json"
    second.write_text(json.dumps(second_scene))
    manifest = tmp_path / "deck-scenes.json"
    manifest.write_text(json.dumps({"title": "Two pages", "slides": [
        {"slide_id": "second", "scene": "second.json"},
        {"slide_id": "first", "scene": "first.json"},
    ]}))
    output = tmp_path / "deck.pptx"
    result = subprocess.run([
        sys.executable, str(SKILL / "scripts" / "slidepoise_runtime.py"), "render-deck",
        "--manifest", str(manifest), "--output", str(output),
    ], text=True, capture_output=True, check=False, cwd=ROOT)
    assert result.returncode == 0, result.stderr or result.stdout
    with zipfile.ZipFile(output) as archive:
        namespace = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        for page, expected in [(1, "second-page-connector"), (2, "first-page-connector")]:
            document = ET.fromstring(archive.read(f"ppt/slides/slide{page}.xml"))
            names = [node.attrib.get("name", "") for node in document.findall(".//p:cNvPr", namespace)]
            assert any(expected in name for name in names), names


def test_connector_polyline_is_one_continuous_powerpoint_object(tmp_path: Path) -> None:
    output = tmp_path / "connector.pptx"
    result = subprocess.run(
        ["node", str(SKILL / "runtime" / "js" / "scene_to_pptx.mjs"), "--input", str(ROOT / "tests" / "fixtures" / "continuous_connector_scene.json"), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    with zipfile.ZipFile(output) as archive:
        slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
    assert slide_xml.count("<a:custGeom>") == 1
    assert slide_xml.count("<a:lnTo>") == 3
    assert slide_xml.count('prst="line"') == 0


def test_setup_updates_unchanged_packaged_files_and_preserves_user_changes(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source-profiles"
    profile = source / "sample"
    (profile / "libraries" / "icons").mkdir(parents=True)
    (profile / "profile.json").write_text(json.dumps({"profile_id": "sample", "name": "Sample"}), encoding="utf-8")
    (profile / "libraries" / "icons" / "catalog.json").write_text(json.dumps({"items": {}}), encoding="utf-8")
    home = tmp_path / "home"
    monkeypatch.setenv("SLIDEPOISE_HOME", str(home))

    first = initialize_home(source)
    assert first["files"]["installed"] >= 2

    installed_profile = home / "profiles" / "sample" / "profile.json"
    packaged_catalog = profile / "libraries" / "icons" / "catalog.json"
    installed_catalog = home / "profiles" / "sample" / "libraries" / "icons" / "catalog.json"
    profile_payload = json.loads((profile / "profile.json").read_text(encoding="utf-8"))
    profile_payload["name"] = "Sample v2"
    (profile / "profile.json").write_text(json.dumps(profile_payload), encoding="utf-8")
    installed_catalog.write_text(json.dumps({"items": {}, "user_note": "keep"}), encoding="utf-8")
    packaged_catalog.write_text(json.dumps({"items": {}, "framework_note": "new"}), encoding="utf-8")

    second = initialize_home(source)
    assert json.loads(installed_profile.read_text(encoding="utf-8"))["name"] == "Sample v2"
    assert json.loads(installed_catalog.read_text(encoding="utf-8"))["user_note"] == "keep"
    assert second["files"]["updated"] >= 1
    assert second["files"]["preserved_user_changes"] >= 1


def test_runtime_node_package_matches_root_dependencies() -> None:
    root_dependencies = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["dependencies"]
    runtime_dependencies = json.loads((FRAMEWORK / "node-runtime-package.json").read_text(encoding="utf-8"))["dependencies"]
    assert runtime_dependencies == root_dependencies


def test_scene_relative_assets_resolve_from_portable_run_root(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    assets.mkdir()
    data.mkdir()
    image = assets / "image.png"
    image.write_bytes(b"image")
    scene_path = data / "scene.json"
    scene = {"objects": [{"id": "image", "kind": "image", "source_path": "assets/image.png"}]}
    resolved = resolve_scene_paths(scene, scene_path)
    assert resolved["objects"][0]["source_path"] == str(image.resolve())


def test_config_migration_preserves_known_and_unrecognized_values(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "config.json"
    source.write_text(json.dumps({
        "schema_version": "2.0.0",
        "remote_sources": {"remix_icon": {"enabled": False}, "wikimedia_commons": {"enabled": False}},
        "measurement": {"segmentation": {"mode": "auto", "checkpoint": None}},
    }), encoding="utf-8")
    destination.write_text(json.dumps({
        "schema_version": "1.0.0",
        "external_icon_fetch": {"enabled": True},
        "measurement": {"segmentation": {"mode": "never", "checkpoint": "/custom/model.pt"}},
        "removed_key": "discard",
    }), encoding="utf-8")
    assert migrate_config(source, destination, tmp_path / "archive")
    migrated = json.loads(destination.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == "2.0.0"
    assert migrated["remote_sources"]["remix_icon"]["enabled"] is True
    assert migrated["measurement"]["segmentation"] == {"mode": "never", "checkpoint": "/custom/model.pt"}
    assert migrated["external_icon_fetch"] == {"enabled": True}
    assert migrated["removed_key"] == "discard"
    assert list((tmp_path / "archive").glob("config-before-2.0.0*.json"))


def test_config_upgrade_adds_generic_density_without_losing_legacy_choices(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "config.json"
    bundled = json.loads((FRAMEWORK / "defaults" / "slidepoise-config.json").read_text(encoding="utf-8"))
    source.write_text(json.dumps(bundled), encoding="utf-8")
    destination.write_text(json.dumps({
        "schema_version": "3.7.0",
        "user_design_overrides": {"editorial-archive": {"style": {"body_font": "Custom Sans", "density": "editorial_balanced"}}},
        "design": {
            "style": {"density": "editorial_balanced"},
            "density_profiles": {"editorial_balanced": {"generation_guidance": ["keep legacy"]}},
        },
    }), encoding="utf-8")
    assert migrate_config(source, destination, tmp_path / "archive")
    migrated = json.loads(destination.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == bundled["schema_version"]
    assert migrated["design"]["style"]["density"] == "editorial_balanced"
    assert migrated["design"]["density_profiles"]["editorial_balanced"]["generation_guidance"] == ["keep legacy"]
    assert migrated["design"]["density_profiles"]["balanced"] == bundled["design"]["density_profiles"]["balanced"]
    assert migrated["user_design_overrides"]["editorial-archive"]["style"]["body_font"] == "Custom Sans"

    session = tmp_path / "session.json"
    resolved = tmp_path / "resolved.json"
    session.write_text(json.dumps({"profile": "editorial-archive"}), encoding="utf-8")
    result = run_script(
        "resolve_config.py",
        "--base", str(destination),
        "--profiles-root", str(PROFILES),
        "--session", str(session),
        "--output", str(resolved),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(resolved.read_text(encoding="utf-8"))["design"]["style"]["density"] == "balanced"


def test_setup_upgrade_retires_single_slide_scope_and_preserves_user_design(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "installed-home"
    home.mkdir()
    monkeypatch.setenv("SLIDEPOISE_HOME", str(home))
    bundled_path = FRAMEWORK / "defaults" / "slidepoise-config.json"
    previous = json.loads(bundled_path.read_text(encoding="utf-8"))
    previous["schema_version"] = "3.9.0"
    previous["scope"]["mode"] = "single_slide"
    previous["user_design_overrides"] = {"consulting": {"style": {"body_font": "Arial"}}}
    previous["design"]["frame"]["header"]["left_text"] = "My practice"
    previous["measurement"]["segmentation"]["mode"] = "never"
    original = json.dumps(previous, indent=2).encode()
    config_path = home / "config.json"
    config_path.write_bytes(original)

    initialize_home(PROFILES)

    migrated = json.loads(config_path.read_text(encoding="utf-8"))
    assert migrated["scope"]["mode"] == "adaptive_presentation"
    assert migrated["user_design_overrides"] == previous["user_design_overrides"]
    assert migrated["design"]["frame"]["header"]["left_text"] == "My practice"
    assert migrated["measurement"]["segmentation"]["mode"] == "never"
    backups = list((home / "archive").glob("config-before-*.json"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == original
    assert run_script("preflight_config.py", str(config_path)).returncode == 0

    initialize_home(PROFILES)
    assert list((home / "archive").glob("config-before-*.json")) == backups


def test_same_schema_legacy_scope_is_repaired_without_resetting_preferences(tmp_path: Path) -> None:
    source = FRAMEWORK / "defaults" / "slidepoise-config.json"
    current = json.loads(source.read_text(encoding="utf-8"))
    current["scope"]["mode"] = "single_slide"
    current["scope"]["default_slide_role"] = "custom_content_role"
    destination = tmp_path / "config.json"
    destination.write_text(json.dumps(current), encoding="utf-8")

    assert migrate_config(source, destination, tmp_path / "archive")
    migrated = json.loads(destination.read_text(encoding="utf-8"))
    assert migrated["scope"] == {"mode": "adaptive_presentation", "default_slide_role": "custom_content_role"}
    assert not migrate_config(source, destination, tmp_path / "archive")


def test_setup_archives_retired_packaged_profile_assets(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source-profiles"
    profile = source / "sample"
    asset = profile / "libraries" / "icons" / "retired.svg"
    asset.parent.mkdir(parents=True)
    (profile / "profile.json").write_text(json.dumps({"profile_id": "sample", "name": "Sample"}), encoding="utf-8")
    asset.write_text("<svg/>", encoding="utf-8")
    home = tmp_path / "home"
    monkeypatch.setenv("SLIDEPOISE_HOME", str(home))
    initialize_home(source)
    asset.unlink()
    second = initialize_home(source)
    assert not (home / "profiles" / "sample" / "libraries" / "icons" / "retired.svg").exists()
    assert list((home / "archive").glob("retired-bundle-*/sample/libraries/icons/retired.svg"))
    assert second["files"]["retired_archived"] == 1
