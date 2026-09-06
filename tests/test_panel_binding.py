import pytest

from framework import panel_binding, run_events
from framework import panel as framework_panel
from framework.storage import write


@pytest.fixture
def runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    result = [tmp_path / "one", tmp_path / "two"]
    for root in result:
        write(root / "session.json", {"name": root.name})
    return result


def test_agent_binding_is_shared_and_survives_reopen(runs):
    initial = panel_binding.ensure(run=runs[0])
    assert panel_binding.get(initial["id"]) == initial
    assert panel_binding.ensure(initial["id"])["run"] == str(runs[0])


def test_agent_switch_preserves_other_conversations(runs):
    first = panel_binding.ensure(run=runs[0])
    second = panel_binding.ensure(run=runs[1])
    switched = panel_binding.ensure(first["id"], runs[1])
    assert switched["run"] == str(runs[1])
    assert switched["revision"] != first["revision"]
    assert panel_binding.get(second["id"]) == second


def test_moved_run_does_not_silently_switch(runs):
    initial = panel_binding.ensure(run=runs[0])
    runs[0].rename(runs[0].with_name("moved"))
    assert panel_binding.ensure(initial["id"])["run"] == str(runs[0])


def test_invalid_binding_and_missing_run_are_rejected(runs):
    with pytest.raises(ValueError):
        panel_binding.ensure("../../config")
    with pytest.raises(FileNotFoundError):
        panel_binding.ensure("missing")
    with pytest.raises(FileNotFoundError):
        panel_binding.ensure(run=runs[0] / "absent")


def test_agent_opens_only_the_bound_style_panel(runs, monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"service":"slidepoise"}'

    monkeypatch.setattr(framework_panel.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())
    result = framework_panel.open_panel(str(runs[0]), view="style")
    assert result["run"] == str(runs[0])
    assert "#" not in result["url"]
    for old_stage in ("plan", "design", "powerpoint"):
        with pytest.raises(ValueError):
            framework_panel.open_panel(str(runs[0]), view=old_stage)
    with pytest.raises(ValueError):
        framework_panel.open_panel()


def test_style_events_are_persistent(runs):
    root = runs[0]
    (root / "work").mkdir()
    event = run_events.record(root, "style_applied", "Session style changed", {"density": "spacious"})
    pending = run_events.pending(root)
    assert pending["events"] == [event]
    assert run_events.acknowledge(root, [event["id"]], pending["revision"])["events"] == []
