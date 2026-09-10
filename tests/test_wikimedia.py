import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'slidepoise/scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def config(tmp_path):
    target = tmp_path / 'config.json'
    target.write_text(json.dumps({'remote_sources': {'wikimedia_commons': {
        'enabled': True, 'api_url': 'https://commons.wikimedia.org/w/api.php',
        'allowed_media_types': ['image/svg+xml', 'image/png'], 'require_license_metadata': True}}}))
    return target


def test_search_reports_api_failure_as_failure(tmp_path, monkeypatch):
    search = module('search_wikimedia_commons')
    monkeypatch.setattr(sys, 'argv', ['search', '--config', str(config(tmp_path)), '--query', 'logo'])
    monkeypatch.setattr(search, 'request_json', lambda url: {'error': {'info': 'Service temporarily unavailable'}})
    with pytest.raises(SystemExit, match='Service temporarily unavailable'):
        search.main()


def test_download_retains_exact_svg_and_provenance(tmp_path, monkeypatch):
    fetch = module('fetch_wikimedia_commons_asset')
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><circle cx="6" cy="6" r="4"/></svg>'
    info = {'mime': 'image/svg+xml', 'url': 'https://upload.wikimedia.org/example.svg',
            'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Example.svg',
            'extmetadata': {'LicenseShortName': {'value': 'Public domain'}, 'Artist': {'value': 'Example author'}}}
    def request(url, accept='*/*'):
        return (json.dumps({'query': {'pages': [{'imageinfo': [info]}]}}).encode(), 'application/json') if 'api.php?' in url else (svg, 'image/svg+xml')
    monkeypatch.setattr(fetch, 'request', request)
    output = tmp_path / 'assets'
    monkeypatch.setattr(sys, 'argv', ['fetch', '--config', str(config(tmp_path)), '--file-title', 'Example.svg', '--asset-id', 'example', '--output-dir', str(output)])
    fetch.main()
    assert (output / 'example.svg').read_bytes() == svg
    provenance = json.loads((output / 'example.svg.provenance.json').read_text())
    assert provenance['license'] == 'Public domain'
    assert provenance['artist'] == 'Example author'
    assert provenance['source_url'] == info['descriptionurl']


@pytest.mark.parametrize('identifier', ['../escape', '/absolute', 'folder/file', '..\\escape'])
def test_download_cannot_write_outside_cache(tmp_path, monkeypatch, identifier):
    fetch = module('fetch_wikimedia_commons_asset')
    monkeypatch.setattr(sys, 'argv', ['fetch', '--config', str(config(tmp_path)), '--file-title', 'Example.svg', '--asset-id', identifier, '--output-dir', str(tmp_path / 'assets')])
    with pytest.raises(SystemExit, match='Asset ID'):
        fetch.main()
    assert not (tmp_path / 'assets').exists()
