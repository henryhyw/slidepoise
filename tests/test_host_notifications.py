from framework import host_notifications, panel_binding, run_events
from framework.storage import read, write


def test_active_bound_task_gets_steered_and_never_started(monkeypatch, tmp_path):
    calls = []
    class Client:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def request(self, method, params):
            calls.append((method, params))
            return {"thread": {"turns": [{"id": "active", "status": "inProgress"}]}}
    monkeypatch.setattr(host_notifications, "CodexProxy", Client)
    status = host_notifications.deliver("explicit-task", tmp_path, {"id": "change", "summary": "Style updated"})
    assert status == "delivered"
    assert [c[0] for c in calls] == ["thread/read", "turn/steer"]
    assert calls[1][1]["expectedTurnId"] == "active"
    assert calls[1][1]["threadId"] == "explicit-task"


def test_idle_task_is_not_started(monkeypatch, tmp_path):
    class Client:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def request(self, method, params):
            assert method == "thread/read"
            return {"thread": {"turns": []}}
    monkeypatch.setattr(host_notifications, "CodexProxy", Client)
    assert host_notifications.deliver("task", tmp_path, {"id": "x", "summary": "x"}) == "waiting_for_checkpoint"


def test_unavailable_transport_preserves_pending_event(monkeypatch, tmp_path):
    import threading
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    run = tmp_path / "run"
    write(run / "session.json", {"name": "Run"})
    panel_binding.ensure(run=run, host_thread_id="bound-task")
    monkeypatch.setattr(host_notifications, "deliver", lambda *_: "waiting_for_checkpoint")
    event = run_events.record(run, "style", "Style updated")
    for thread in threading.enumerate():
        if thread.name == "slidepoise-host-notification": thread.join(timeout=2)
    pending = run_events.pending(run)["events"]
    assert pending[0]["id"] == event["id"]
    assert pending[0]["delivery"] == {"bound-task": "waiting_for_checkpoint"}
    assert pending[0]["status"] == "pending"


def test_browser_binding_never_inherits_server_task(monkeypatch, tmp_path):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CODEX_THREAD_ID", "server-task")
    run = tmp_path / "run"
    write(run / "session.json", {"name": "Run"})
    assert "host_thread_id" not in panel_binding.ensure(run=run)


def test_invalid_binding_does_not_block_a_user_change(monkeypatch, tmp_path):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    run = tmp_path / "run"
    write(run / "session.json", {"name": "Run"})
    write(tmp_path / "home/panels/invalid.json", ["not a binding"])
    event = run_events.record(run, "style", "Style updated")
    assert run_events.pending(run)["events"][0]["id"] == event["id"]
