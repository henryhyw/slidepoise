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


def test_console_reference_search_uses_live_metadata_and_source_restrictions(service):
    from io import BytesIO
    from PIL import Image
    _, request = service
    image = BytesIO()
    Image.new('RGB', (12, 12), 'white').save(image, 'PNG')
    created = {}
    for origin in ['published_document', 'user_private_document', 'generated_image', 'unknown']:
        status, _, raw = request('POST', '/api/profile/reference/add', {
            'profile_id':'consulting', 'filename':'reference.png', 'name':origin,
            'description':'Orchestration architecture and data flow', 'tags':['architecture'],
            'source_type':origin, 'source_url':'https://example.org/report.pdf', 'source_page':'12',
            'content_base64':base64.b64encode(image.getvalue()).decode()})
        assert status == 201
        created[origin] = json.loads(raw)['id']
    query = '/api/reference-search?' + urlencode({'profile':'consulting','query':'orchestration architecture'})
    status, _, raw = request('GET', query)
    assert status == 200
    result = json.loads(raw)
    ids = {item['id'] for item in result['items']}
    assert created['published_document'] in ids and created['user_private_document'] in ids
    assert created['generated_image'] not in ids and created['unknown'] not in ids
    assert result['selection_owner'] == 'host_agent'
    _, _, raw = request('GET', query + '&authenticity=any')
    assert set(created.values()) <= {item['id'] for item in json.loads(raw)['items']}
    _, _, raw = request('GET', '/api/library?kind=visual_references&profile=consulting')
    status, _, _ = request('POST', '/api/profile/reference/update', {
        'profile_id':'consulting', 'id':created['published_document'],
        'revision':json.loads(raw)['revision'], 'values':{'retrieval_eligible':False}})
    assert status == 200
    _, _, raw = request('GET', query)
    assert created['published_document'] not in {item['id'] for item in json.loads(raw)['items']}
    assert request('GET', query + '&authenticity=unsupported')[0] == 400


def test_shared_resource_selection_and_edits_remain_live_across_profiles(service):
    from io import BytesIO
    from PIL import Image
    _, request = service

    def read(route):
        status, _, raw = request('GET', route)
        assert status == 200, raw
        return json.loads(raw)

    def post(route, payload):
        status, _, raw = request('POST', route, payload)
        assert status in {200, 201}, raw
        return json.loads(raw)

    image = BytesIO()
    Image.new('RGB', (12, 12), 'white').save(image, 'PNG')
    encoded = base64.b64encode(image.getvalue()).decode()
    refs = post('/api/library-set/create', {'name': 'Shared test references', 'kind': 'visual_references'})
    icons = post('/api/library-set/create', {'name': 'Shared test icons', 'kind': 'icons'})

    def add(set_id, name):
        return post('/api/library-set/add', {'set_id': set_id, 'filename': 'resource.png',
            'content_base64': encoded, 'name': name, 'description': 'Shared decision reference',
            'source_type': 'user_private_document', 'source_page': '3', 'license': 'User supplied'})

    first = add(refs['id'], 'First reference')
    second = add(refs['id'], 'Second reference')
    add(icons['id'], 'Private brand icon')
    for profile_id, subset, enabled_icons in [('consulting', None, [icons['id']]), ('editorial-archive', [first['id']], [])]:
        profile = read('/api/profile?profile=' + profile_id)
        post('/api/profile/update', {'profile_id': profile_id, 'revision': profile['revision'], 'values': {
            'library_sets': {'visual_references': [refs['id']], 'icons': enabled_icons, 'components': []},
            'library_items': {'visual_references': {} if subset is None else {refs['id']: subset}, 'icons': {}, 'components': {}}}})
    third = add(refs['id'], 'Added later')
    all_refs = read('/api/library?kind=visual_references&profile=consulting')['items']
    subset = read('/api/library?kind=visual_references&profile=editorial-archive')['items']
    assert {item['id'] for item in all_refs} == {first['id'], second['id'], third['id']}
    assert [item['id'] for item in subset] == [first['id']]
    assert subset[0]['resource_id'] == f"{refs['id']}:{first['id']}"
    assert subset[0]['provenance']['source_type'] == 'user_private_document'
    assert read('/api/library?kind=icons&profile=editorial-archive')['items'] == []
    assert len(read('/api/library?kind=icons&profile=consulting')['items']) == 1
    post('/api/library-set/item/update', {'set_id': refs['id'], 'id': first['id'],
        'revision': subset[0]['catalog_revision'], 'values': {'name': 'Updated shared reference'}})
    for profile_id in ['consulting', 'editorial-archive']:
        items = read('/api/library?kind=visual_references&profile=' + profile_id)['items']
        assert next(item for item in items if item['id'] == first['id'])['name'] == 'Updated shared reference'
    status, _, _ = request('POST', '/api/library-set/item/update', {'set_id': refs['id'], 'id': first['id'],
        'revision': subset[0]['catalog_revision'], 'values': {'name': 'Stale overwrite'}})
    assert status == 409
    selection = read('/api/design?profile=editorial-archive')
    assert selection['selected_sets']['visual_references'] == [refs['id']]
    assert selection['selected_items']['visual_references'] == {refs['id']: [first['id']]}


def test_shared_resource_edit_uses_item_identity_and_safe_source_paths(service):
    from framework import library_sets
    _, request = service
    path, catalog = library_sets.set_catalog('consulting-references')
    item = next(iter(catalog['items'].values()))
    item_id = item['id']
    # Historical catalogs use filenames as dictionary keys and IDs inside records.
    assert item_id not in catalog['items']
    status, _, raw = request('GET', '/api/library-set?set_id=consulting-references')
    assert status == 200
    payload = json.loads(raw)
    status, _, raw = request('POST', '/api/library-set/item/update', {
        'set_id': 'consulting-references', 'id': item_id,
        'revision': payload['catalog_revision'], 'values': {'description': 'Shared guidance'}})
    assert status == 200, raw
    updated = json.loads(raw)
    assert next(item for item in updated['items'] if item['id'] == item_id)['description'] == 'Shared guidance'
    status, _, _ = request('POST', '/api/library-set/item/update', {
        'set_id': 'consulting-references', 'id': item_id,
        'revision': updated['catalog_revision'], 'values': {'path': '../outside.png'}})
    assert status == 400
