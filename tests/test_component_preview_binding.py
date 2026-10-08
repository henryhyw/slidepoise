"""Native component previews stay bound to their source and selected page."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'slidepoise/scripts'), str(ROOT / 'slidepoise/runtime/src')]
import component_preview
from prepare_generation import augment_selected_components
from slidepoise.reconstruction.scene import _component_record


def test_preview_reuse_requires_matching_source_page_and_preview(tmp_path, monkeypatch):
    source, preview = tmp_path / 'source.pptx', tmp_path / 'preview.png'
    source.write_bytes(b'first source')
    calls = []

    def render(command, **kwargs):
        calls.append(command)
        Path(command[command.index('--output') + 1]).write_bytes(f'page {command[-1]} source {source.read_bytes()}'.encode())
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(component_preview.subprocess, 'run', render)
    component_preview.ensure_preview(source, preview, 2)
    component_preview.ensure_preview(source, preview, 2)
    assert len(calls) == 1
    source.write_bytes(b'changed source')
    component_preview.ensure_preview(source, preview, 2)
    assert len(calls) == 2
    component_preview.ensure_preview(source, preview, 3)
    assert len(calls) == 3
    preview.write_bytes(b'stale or overwritten preview')
    component_preview.ensure_preview(source, preview, 3)
    assert len(calls) == 4
    preview.with_suffix('.png.source.json').write_text('{malformed')
    component_preview.ensure_preview(source, preview, 3)
    assert len(calls) == 5


def test_catalog_native_source_and_page_resolve_consistently(tmp_path, monkeypatch):
    source = tmp_path / 'shared.pptx'
    source.write_bytes(b'donor')
    catalog = tmp_path / 'catalog.json'
    catalog.write_text(json.dumps({'native_source':'shared.pptx', 'items': {
        'chart': {'id':'chart', 'kind':'chart', 'native_source_slide_number':4,
                  'grammar': {'native_constructor_defaults': {}}}}}))

    def render(command, **kwargs):
        Path(command[command.index('--output') + 1]).write_bytes(b'preview of fourth page')
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(component_preview.subprocess, 'run', render)
    libraries = {'components': {'catalog':str(catalog)}}
    selected = augment_selected_components({'selected_components':[{'component_id':'chart','reason':'A native chart structure suited to the selected data'}]}, libraries=libraries)['selected_components'][0]
    _, reconstructed = _component_record('chart', 'chart', {'resource_catalogs':libraries})
    assert selected['canonical_file'] == reconstructed['native_donor_path'] == str(source)
    assert selected['preview_file'] == reconstructed['preview_path'] == str(tmp_path / 'shared.slide-4.preview.png')
    assert selected['native_source_binding']['slide_number'] == reconstructed['native_source_slide_number'] == 4
    assert selected['native_source_binding']['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
