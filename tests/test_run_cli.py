import json
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path

import pytest

from framework import cli, run_events, run_versions, storage


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    root = tmp_path / "presentation"
    storage.write(root / "session.json", {"id": "example", "name": "Example"})
    storage.write(root / "session-overrides.json", {"profile": "consulting"})
    storage.write(root / "work/session-defaults.json", {"captured_at": "test"})
    return root


def invoke(capsys, *arguments):
    args = cli.parser().parse_args(["run", *map(str, arguments)])
    args.func(args)
    return json.loads(capsys.readouterr().out)


def test_cli_adopts_only_seen_events_and_keeps_later_changes_pending(run, capsys):
    first = run_events.record(run, "session_setting_applied", "Typography changed", {"body_font": "Georgia"})
    snapshot = invoke(capsys, "sync", run)
    second = run_events.record(run, "asset_added", "Reference added", {"path": "uploads/reference.png"})
    with pytest.raises(storage.ConflictError):
        invoke(capsys, "ack-events", run, "--ids", first["id"], "--expected", snapshot["events"]["revision"])
    current = invoke(capsys, "events", run)
    assert [event["id"] for event in current["events"]] == [first["id"], second["id"]]
    remaining = invoke(capsys, "ack-events", run, "--ids", first["id"], "--expected", current["revision"])
    assert [event["id"] for event in remaining["events"]] == [second["id"]]
    saved = storage.read(run / "work/panel-events.json")
    assert [event["status"] for event in saved["events"]] == ["acknowledged", "pending"]


def test_sync_leaves_legacy_history_intact_without_reintroducing_stage_state(run, capsys):
    legacy = {"activity.json": {"entries": [{"message": "Preserve this authored note"}]},
              "stage-selections.json": {"design": "iteration-old"}}
    for name, value in legacy.items():
        storage.write(run / "work" / name, value)
    snapshot = invoke(capsys, "sync", run)
    assert snapshot["overrides"] == {"profile": "consulting"}
    assert snapshot["metadata_revision"] == storage.revision(run / "session.json")
    assert not {"activity", "stage_selection", "selection_revision"} & snapshot.keys()
    archived = Path(invoke(capsys, "archive", run)["path"])
    for name, value in legacy.items():
        assert storage.read(run / "work" / name) == value
        assert storage.read(archived / "work" / name) == value


def test_settings_snapshot_cannot_pair_old_values_with_a_new_write_token(run, monkeypatch):
    target = run / "session-overrides.json"
    before = storage.revision(target)
    read_started = threading.Event()
    resume_read = threading.Event()
    write_started = threading.Event()
    original_read = cli.read

    def paused_read(path, default=None):
        value = original_read(path, default)
        if path == target:
            read_started.set()
            assert resume_read.wait(3), "Settings reader did not resume"
        return value

    def write_new_settings():
        write_started.set()
        storage.update(target, lambda _: {"profile": "editorial-archive"}, expected=before)

    monkeypatch.setattr(cli, "read", paused_read)
    with ThreadPoolExecutor(max_workers=2) as executor:
        reading = executor.submit(cli.run_settings, run)
        assert read_started.wait(3)
        writing = executor.submit(write_new_settings)
        assert write_started.wait(3)
        try:
            with pytest.raises(TimeoutError):
                writing.result(timeout=0.1)
        finally:
            resume_read.set()
        snapshot = reading.result(timeout=3)
        writing.result(timeout=3)
    assert snapshot["overrides"] == {"profile": "consulting"}
    assert snapshot["overrides_revision"] == before
    assert storage.read(target) == {"profile": "editorial-archive"}
    assert storage.revision(target) != snapshot["overrides_revision"]


def test_failed_archive_does_not_publish_a_partial_snapshot(run, monkeypatch):
    previous = Path(run_versions.archive(run)["path"])
    original_copy = run_versions.shutil.copy2

    def fail_late(source, destination, *args, **kwargs):
        if Path(source) == run / "session.json":
            raise OSError("Simulated disk failure")
        return original_copy(source, destination, *args, **kwargs)

    monkeypatch.setattr(run_versions.shutil, "copy2", fail_late)
    with pytest.raises(OSError, match="disk failure"):
        run_versions.archive(run)
    assert list((run / "history").iterdir()) == [previous]
    assert storage.read(previous / "session.json") == storage.read(run / "session.json")
