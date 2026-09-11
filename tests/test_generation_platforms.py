"""Cross-host settings, capability checks and lossless manual image exchanges."""
import json
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from framework import image_generation, installer, sessions
from framework.paths import BUNDLED_PROFILES_ROOT
from framework.profiles import initialize_home
from framework.storage import ConflictError
from test_generation_request import compiled_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'slidepoise/scripts'))
from generation_handoff import export_bundle, import_result, route
from prepare_image_edit import build_edit_request
from slidepoise.generation import compatible_tools, preferences


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('SLIDEPOISE_HOME', str(tmp_path / 'home'))
    initialize_home(BUNDLED_PROFILES_ROOT)
    return tmp_path / 'home'


def test_saved_preferences_freeze_per_run_and_can_be_overridden(home, tmp_path):
    first = sessions.create('First', str(tmp_path / 'first'))
    before = image_generation.payload()
    image_generation.configure({'mode': 'manual'}, before['revision'])
    with pytest.raises(ConflictError):
        image_generation.configure({'mode': 'auto'}, before['revision'])
    second = sessions.create('Second', str(tmp_path / 'second'))
    assert sessions.resolve(first)['generation']['preferences']['mode'] == 'auto'
    assert sessions.resolve(second)['generation']['preferences']['mode'] == 'manual'
    from framework.cli import run_settings
    saved = run_settings(first)
    saved['overrides']['image_generation'] = {'mode': 'tool', 'tool': 'mcp__studio__image'}
    sessions.save_overrides(first, saved['overrides'], saved['overrides_revision'])
    assert sessions.resolve(first)['generation']['preferences']['tool'] == 'mcp__studio__image'
    assert image_generation.payload()['values']['mode'] == 'manual'


@pytest.mark.parametrize('host,directory', [('codex', '.codex'), ('claude', '.claude'), ('qoder', '.qoder')])
def test_host_install_is_self_contained_and_preserves_prior_edits(home, tmp_path, monkeypatch, host, directory):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path / 'user'))
    target = Path(installer.install_skill_for(host))
    assert target == tmp_path / 'user' / directory / 'skills/slidepoise'
    assert (target / 'scripts/generation_handoff.py').is_file()
    assert (target / 'runtime/src/slidepoise/generation.py').is_file()
    assert (target / 'references/image-generation.md').is_file()
    installer.install_skill_for(host)
    assert not list((home / 'archive').glob(f'{host}-skill-*'))
    (target / 'SKILL.md').write_text('User customisation')
    installer.install_skill_for(host)
    archives = list((home / 'archive').glob(f'{host}-skill-*'))
    assert len(archives) == 1 and (archives[0] / 'SKILL.md').read_text() == 'User customisation'


def test_detection_does_not_claim_image_generation(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(installer.shutil, 'which', lambda name: '/bin/claude' if name == 'claude' else None)
    (tmp_path / '.qoder').mkdir()
    hosts = installer.detect_host()
    assert hosts['agents']['claude']['detected']
    assert hosts['agents']['qoder']['detected']
    assert not hosts['agents']['codex']['detected']
    assert 'current conversation' in hosts['image_generation']


def test_capability_selection_does_not_drop_references_or_substitute_tools(compiled_request):
    request = json.loads(compiled_request.read_text())
    tools = {'tools': [
        {'id': 'native', 'available': True, 'operations': ['generate'], 'reference_images': False},
        {'id': 'mcp__image', 'available': True, 'operations': ['generate', 'edit'], 'reference_images': True},
        {'id': 'limited', 'available': True, 'operations': ['generate'], 'reference_images': True, 'max_prompt_chars': 10},
    ]}
    facts = compatible_tools(request, tools, preferences())
    assert [t['id'] for t in facts if t['compatible']] == ['mcp__image']
    assert route(compiled_request, tools, 'mcp__image')['available']
    assert not route(compiled_request, tools, 'native')['available']
    assert route(compiled_request, tools)['selected_tool'] is None
    model = compatible_tools(request, tools, preferences({'model': 'unconfirmed'}))
    assert not any(t['compatible'] for t in model)


def test_manual_bundle_keeps_prompt_bytes_and_all_references_and_resumes(compiled_request, tmp_path):
    request = json.loads(compiled_request.read_text())
    result = export_bundle(compiled_request, tmp_path / 'exchange')
    with zipfile.ZipFile(result['bundle']) as bundle:
        assert bundle.read('prompt.txt') == request['prompt'].encode()
        refs = json.loads(bundle.read('request.json'))['references']
        assert len(refs) == len(request['reference_images'])
        for packaged, original in zip(refs, request['reference_images']):
            assert bundle.read(packaged['file']) == Path(original['path']).read_bytes()
        assert str(tmp_path).encode() not in bundle.read('request.json')
        assert 'handoff.json' not in bundle.namelist()
    returned = tmp_path / 'user-result.webp'
    Image.new('RGBA', (128, 64), (200, 20, 30, 120)).save(returned, lossless=True)
    candidate = tmp_path / 'candidate.png'
    evidence = import_result(Path(result['folder']), returned, candidate)
    assert Image.open(candidate).getpixel((2, 2)) == (200, 20, 30, 120)
    assert evidence['review_required']
    assert evidence['alpha_range'] == [120, 120]
    with pytest.raises(ValueError, match='already exists'):
        import_result(Path(result['folder']), returned, candidate)


def test_manual_exchange_refuses_changed_inputs(compiled_request, tmp_path):
    export_bundle(compiled_request, tmp_path / 'exchange')
    Image.new('RGB', (10, 10)).save(tmp_path / 'returned.png')
    (tmp_path / 'intent.json').write_text('{}')
    with pytest.raises(SystemExit, match='input changed'):
        import_result(tmp_path / 'exchange', tmp_path / 'returned.png', tmp_path / 'candidate.png')
    assert not (tmp_path / 'candidate.png').exists()


def test_manual_exchange_refuses_changed_bundle(compiled_request, tmp_path):
    export_bundle(compiled_request, tmp_path / 'exchange')
    (tmp_path / 'exchange/bundle/prompt.txt').write_text('Different prompt')
    Image.new('RGB', (10, 10)).save(tmp_path / 'returned.png')
    with pytest.raises(ValueError, match='exported prompt'):
        import_result(tmp_path / 'exchange', tmp_path / 'returned.png', tmp_path / 'candidate.png')


def test_focused_edits_export_candidate_first(compiled_request, tmp_path):
    Image.new('RGB', (128, 64)).save(tmp_path / 'candidate.png')
    (tmp_path / 'changes.txt').write_text('Preserve the approved title.')
    request = build_edit_request(compiled_request, tmp_path / 'candidate.png', tmp_path / 'changes.txt')
    edit = tmp_path / 'edit.json'
    edit.write_text(json.dumps(request))
    result = export_bundle(edit, tmp_path / 'exchange')
    with zipfile.ZipFile(result['bundle']) as archive:
        manifest = json.loads(archive.read('request.json'))
        assert 'current-candidate' in manifest['references'][0]['file']
        assert archive.read(manifest['references'][0]['file']) == (tmp_path / 'candidate.png').read_bytes()


def test_transparent_illustration_uses_the_same_manual_exchange(tmp_path):
    import subprocess
    from test_raster_sources import fixture
    returned, target, _, semantic = fixture(tmp_path)
    root = Path(__file__).resolve().parents[1]
    config = root / 'framework/defaults/slidepoise-config.json'
    semantic_path = tmp_path / 'semantic.json'
    semantic_path.write_text(json.dumps(semantic))
    result = subprocess.run([sys.executable, str(root / 'slidepoise/scripts/prepare_illustration_refinement.py'),
                            '--image', str(target), '--semantic-map', str(semantic_path), '--config', str(config),
                            '--output-dir', str(tmp_path / 'crops'), '--board', str(tmp_path / 'board.png'),
                            '--review-board', str(tmp_path / 'review.png'), '--manifest', str(tmp_path / 'manifest.json'),
                            '--brief', str(tmp_path / 'brief.md')], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    request = next((tmp_path / 'crops').rglob('*.request.json'))
    export_bundle(request, tmp_path / 'exchange')
    Image.new('RGBA', (120, 100), (20, 30, 40, 128)).save(tmp_path / 'no-backdrop.png')
    with pytest.raises(ValueError, match='transparent'):
        import_result(tmp_path / 'exchange', tmp_path / 'no-backdrop.png', tmp_path / 'invalid.png')
    imported = import_result(tmp_path / 'exchange', returned, tmp_path / 'imported.png')
    assert imported['alpha_range'] == [0, 255]
    from extract_refined_illustrations import extract
    from apply_illustration_sources import apply_sources
    mapping = extract(tmp_path / 'imported.png', json.loads((tmp_path / 'manifest.json').read_text()), 'art', tmp_path / 'assets')
    updated, ids = apply_sources(semantic, mapping)
    assert ids == ['art']
    assert updated['entities'][0]['bbox_hint'] == semantic['entities'][0]['bbox_hint']


def test_upgrade_replaces_host_policy_without_rewriting_captured_runs(home, tmp_path):
    from framework.storage import read, write
    config = read(home / 'config.json')
    config['generation'].pop('preferences')
    config['generation']['host_adapter'] = {'mode': 'host_native_or_delegated_image_generation', 'max_prompt_chars': 40000,
                                           'unsupported_host_policy': 'stop', 'codex': 'old host instructions'}
    write(home / 'config.json', config)
    run = sessions.create('Before upgrade', str(tmp_path / 'old'))
    frozen = (run / 'work/session-defaults.json').read_bytes()
    initialize_home(BUNDLED_PROFILES_ROOT)
    new = read(home / 'config.json')['generation']
    assert new['preferences']['mode'] == 'auto'
    assert new['host_adapter'] == {'mode': 'agent_discovered_or_manual', 'max_prompt_chars': 40000}
    assert (run / 'work/session-defaults.json').read_bytes() == frozen
    from framework.cli import run_settings
    saved = run_settings(run)
    saved['overrides']['generation_model'] = 'my-existing-model'
    sessions.save_overrides(run, saved['overrides'], saved['overrides_revision'])
    assert sessions.resolve(run)['generation']['preferences']['model'] == 'my-existing-model'
