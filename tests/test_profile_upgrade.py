"""Upgrade saved profiles without discarding user choices or captured designs."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from framework import design, profiles, sessions
from framework.paths import BUNDLED_PROFILES_ROOT
from framework.storage import read, write

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('old,new', [('personal-website', 'editorial-archive'), ('personal-monochrome', 'monochrome-modern')])
def test_upgrade_preserves_settings_assets_and_captured_sessions(tmp_path, monkeypatch, old, new):
    home = tmp_path / 'home'
    monkeypatch.setenv('SLIDEPOISE_HOME', str(home))
    profiles.initialize_home(BUNDLED_PROFILES_ROOT)
    legacy = home / 'profiles' / old
    (home / 'profiles' / new).rename(legacy)
    profile = read(legacy / 'profile.json')
    profile['profile_id'] = old
    profile['purpose'] = 'My custom direction'
    write(legacy / 'profile.json', profile)
    extra = legacy / 'libraries/visual_references/custom.txt'
    extra.write_text('User-owned resource')
    manifest = read(home / 'manifest.json')
    manifest['files'] = {k.replace(f'profiles/{new}/', f'profiles/{old}/'): v for k, v in manifest['files'].items()}
    write(home / 'manifest.json', manifest)
    config = read(home / 'config.json')
    config['design']['profile'] = old
    config['user_design_overrides'] = {old: {'style': {'body_font': 'Courier New'}}}
    config['library_locations'] = {old: {'visual_references': str(legacy / 'libraries/visual_references')}}
    write(home / 'config.json', config)
    write(home / 'settings.json', {'active_profile': old})
    captured = sessions.create('Before upgrade', location=tmp_path / 'deck', profile=old)
    capture_bytes = (captured / 'work/session-defaults.json').read_bytes()
    profiles.initialize_home(BUNDLED_PROFILES_ROOT)
    assert not legacy.exists()
    assert (home / 'profiles' / new / 'libraries/visual_references/custom.txt').read_text() == 'User-owned resource'
    assert profiles.profile_record(new)['profile']['purpose'] == 'My custom direction'
    assert profiles.active_profile_id() == new
    assert profiles.profile_record(old)['id'] == new
    assert design.resolve_default(old)['design']['style']['body_font'] == 'Courier New'
    resolved = sessions.resolve(captured)
    assert resolved['design']['profile'] == old
    assert resolved['design']['style']['body_font'] == 'Courier New'
    assert Path(resolved['libraries']['visual_references']['catalog']).is_file()
    assert (captured / 'work/session-defaults.json').read_bytes() == capture_bytes
    config_after = (home / 'config.json').read_bytes()
    profiles.initialize_home(BUNDLED_PROFILES_ROOT)
    assert (home / 'config.json').read_bytes() == config_after
    new_run = sessions.create('After upgrade', location=tmp_path / 'new-deck', profile=old)
    assert read(new_run / 'session-overrides.json')['profile'] == new


def test_name_collision_preserves_both_profiles(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    monkeypatch.setenv('SLIDEPOISE_HOME', str(home))
    profiles.initialize_home(BUNDLED_PROFILES_ROOT)
    old = home / 'profiles/personal-website'
    shutil.copytree(home / 'profiles/editorial-archive', old)
    payload = read(old / 'profile.json')
    payload.update(profile_id='personal-website', purpose='Independent custom style')
    write(old / 'profile.json', payload)
    write(home / 'settings.json', {'active_profile': 'personal-website'})
    profiles.initialize_home(BUNDLED_PROFILES_ROOT)
    assert profiles.active_profile_id() == 'personal-website'
    assert profiles.profile_record('personal-website')['profile']['purpose'] == 'Independent custom style'
    assert (home / 'profiles/editorial-archive/profile.json').is_file()


def test_packaged_resolver_accepts_old_profile_name(tmp_path):
    session = tmp_path / 'session.json'
    write(session, {'profile': 'personal-website'})
    output = tmp_path / 'resolved.json'
    subprocess.run([sys.executable, str(ROOT / 'slidepoise/scripts/resolve_config.py'),
                    '--base', str(ROOT / 'framework/defaults/slidepoise-config.json'),
                    '--profiles-root', str(BUNDLED_PROFILES_ROOT), '--session', str(session),
                    '--output', str(output)], check=True, capture_output=True)
    assert read(output)['design']['profile'] == 'editorial-archive'
    assert Path(read(output)['libraries']['visual_references']['catalog']).is_file()
