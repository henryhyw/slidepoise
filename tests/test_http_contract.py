"""Exercise the real local service over HTTP with an isolated presentation home."""

import base64
from html.parser import HTMLParser
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode, urljoin

import pytest

from framework import run_events, sessions
from framework.paths import BUNDLED_PROFILES_ROOT
from framework.profiles import initialize_home
from framework.storage import revision
from webapp import server


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(BUNDLED_PROFILES_ROOT)
    run = sessions.create("HTTP integration", location=str(tmp_path / "presentation"))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()

    def request(method, path, payload=None, headers=None):
        connection = HTTPConnection(*httpd.server_address, timeout=5)
        try:
            encoded = json.dumps(payload).encode() if payload is not None else None
            connection.request(method, path, body=encoded, headers={"Content-Type": "application/json", **(headers or {})})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    yield run, request
    httpd.shutdown()
    thread.join(timeout=5)
    httpd.server_close()


class LinkedAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.urls.append((attrs["src"], "javascript"))
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append((attrs["href"], "text/css"))


def test_console_and_panel_serve_their_linked_assets_with_matching_head_responses(service):
    _, request = service
    for route in ("/", "/console/"):
        status, headers, content = request("GET", route)
        assert status == 200 and headers["Content-Type"].startswith("text/html")
        assets = LinkedAssets()
        assets.feed(content.decode())
        assert assets.urls
        for target, expected_type in [(route, "text/html"), *assets.urls]:
            path = urljoin(route, target)
            status, headers, content = request("GET", path)
            head_status, head_headers, head_content = request("HEAD", path)
            assert status == head_status == 200, path
            assert expected_type in headers["Content-Type"], path
            assert head_headers["Content-Type"] == headers["Content-Type"]
            assert int(head_headers["Content-Length"]) == len(content)
            assert head_content == b""


def test_api_and_artifact_head_share_get_status_and_path_boundaries(service, tmp_path):
    run, request = service
    (run / "uploads" / "source.txt").write_text("Reference material", encoding="utf-8")
    outside = tmp_path / "private.txt"
    outside.write_text("Outside the presentation", encoding="utf-8")
    cases = [
        ("/../server.py", 200),
        ("/api/context", 200),
        ("/api/artifact?" + urlencode({"run": run, "path": "uploads/source.txt"}), 200),
        ("/api/artifact?" + urlencode({"run": run, "path": "../private.txt"}), 404),
        ("/api/artifact?" + urlencode({"run": run, "path": outside}), 404),
        ("/api/panel/binding?id=missing", 404),
    ]
    for path, expected in cases:
        status, headers, body = request("GET", path)
        head_status, head_headers, head_body = request("HEAD", path)
        assert status == head_status == expected, path
        assert head_headers["Content-Type"] == headers["Content-Type"]
        assert int(head_headers["Content-Length"]) == len(body)
        assert head_body == b""
        assert outside.read_bytes() not in body


def test_style_save_is_scoped_and_conflicts_do_not_overwrite_newer_changes(service):
    run, request = service
    before_profile = sessions.resolve(run)["design"]["style"]["body_font"]
    saved_revision = revision(run / "session-overrides.json")
    body = {"run": str(run), "values": {"body_font": "Courier New"}, "revision": saved_revision}
    status, _, content = request("POST", "/api/run/design", body)
    assert status == 200
    assert json.loads(content)["values"]["body_font"] == "Courier New"
    body["values"]["body_font"] = "Georgia"
    status, _, content = request("POST", "/api/run/design", body)
    assert status == 409 and json.loads(content)["error"]
    status, _, content = request("GET", "/api/run?" + urlencode({"path": run}))
    assert status == 200
    assert json.loads(content)["values"]["body_font"] == "Courier New"
    assert len(run_events.pending(run)["events"]) == 1
    sibling = sessions.create("Unchanged", location=str(run.parent / "sibling"))
    assert sessions.resolve(sibling)["design"]["style"]["body_font"] == before_profile


def test_console_style_save_keeps_values_and_guidance_together(service, monkeypatch):
    from framework import design
    from framework.paths import data_home
    from framework.profiles import profile_record
    run, request = service
    before_run = sessions.resolve(run)
    _, _, content = request("GET", "/api/design?profile=consulting")
    initial = json.loads(content)
    paths = [data_home() / "config.json", Path(profile_record("consulting")["path"])]
    original = [path.read_bytes() for path in paths]
    body = {"profile": "consulting", "values": {"body_font": "Courier New"},
            "profile_values": {"style_agency": {"typography": "guided"}},
            "revision": initial["revision"], "profile_revision": initial["profile_revision"]}
    bad = {**body, "values": {"primary": "invalid"}}
    assert request("POST", "/api/profile/style", bad)[0] == 400
    assert [path.read_bytes() for path in paths] == original

    real_write = design.write
    def failing_config_write(path, value):
        if path == paths[0]:
            raise OSError("Simulated write failure")
        real_write(path, value)
    with monkeypatch.context() as patch:
        patch.setattr(design, "write", failing_config_write)
        assert request("POST", "/api/profile/style", body)[0] == 400
    assert [path.read_bytes() for path in paths] == original

    status, _, content = request("POST", "/api/profile/style", body)
    assert status == 200
    saved = json.loads(content)
    assert saved["values"]["body_font"] == "Courier New"
    assert saved["style_agency"]["typography"] == "guided"
    assert saved["style_agency"]["icon_treatment"] == initial["style_agency"]["icon_treatment"]
    committed = [path.read_bytes() for path in paths]
    for stale in ({**body, "revision": saved["revision"]}, {**body, "profile_revision": saved["profile_revision"]}):
        assert request("POST", "/api/profile/style", stale)[0] == 409
        assert [path.read_bytes() for path in paths] == committed
    newer = sessions.create("New defaults", location=run.parent / "new-defaults")
    assert sessions.resolve(newer)["design"]["style"]["body_font"] == "Courier New"
    assert sessions.resolve(newer)["resolved_profile"]["style_agency"]["typography"] == "guided"
    assert sessions.resolve(run)["design"] == before_run["design"]


def test_foreign_origin_cannot_write_and_uploaded_asset_round_trips_through_panel(service):
    run, request = service
    content = b"Source material for the presentation"
    payload = {"run": str(run), "filename": "../brief.txt", "content_base64": base64.b64encode(content).decode()}
    status, _, _ = request("POST", "/api/upload", payload, {"Origin": "https://example.invalid"})
    assert status == 400
    assert list((run / "uploads").iterdir()) == []
    assert run_events.pending(run)["events"] == []
    status, _, body = request("POST", "/api/upload", payload)
    assert status == 201
    uploaded = Path(json.loads(body)["path"])
    assert uploaded.parent == run / "uploads"
    assert uploaded.read_bytes() == content
    status, _, body = request("GET", "/api/panel?" + urlencode({"run": run}))
    assert status == 200
    material = next(item for item in json.loads(body)["materials"] if item["name"] == uploaded.name)
    status, _, downloaded = request("GET", material["url"])
    assert status == 200 and downloaded == content
    assert [item["kind"] for item in run_events.pending(run)["events"]] == ["asset_added"]


def test_generation_preferences_are_shared_revisioned_and_validated(service):
    _, request = service
    status, _, body = request('GET', '/api/generation')
    assert status == 200
    initial = json.loads(body)
    status, _, body = request('POST', '/api/generation', {'values': {'mode': 'manual'}, 'revision': initial['revision']})
    assert status == 200 and json.loads(body)['values']['mode'] == 'manual'
    status, _, _ = request('POST', '/api/generation', {'values': {'mode': 'auto'}, 'revision': initial['revision']})
    assert status == 409
    current = json.loads(request('GET', '/api/generation')[2])
    status, _, _ = request('POST', '/api/generation', {'values': {'mode': 'tool', 'tool': ''}, 'revision': current['revision']})
    assert status == 400
    assert json.loads(request('GET', '/api/generation')[2])['values']['mode'] == 'manual'
