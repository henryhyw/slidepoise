from types import SimpleNamespace
from framework import preview_install


def test_ready_installation_never_invokes_package_manager(monkeypatch):
    monkeypatch.setattr(preview_install, 'preview_status', lambda: {'office': '/bin/soffice', 'pdftoppm': '/bin/pdftoppm'})
    monkeypatch.setattr(preview_install.subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(AssertionError('unexpected install')))
    assert preview_install.install_preview_tools()['status'] == 'ready'


def test_installation_rechecks_executables_and_reports_partial_failure(monkeypatch):
    states = iter([{'office': None, 'pdftoppm': '/bin/pdftoppm'}, {'office': None, 'pdftoppm': '/bin/pdftoppm'}])
    monkeypatch.setattr(preview_install, 'preview_status', lambda: next(states))
    monkeypatch.setattr(preview_install, 'installation_commands', lambda missing: ([['manager', 'office']], None))
    monkeypatch.setattr(preview_install.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1))
    result = preview_install.install_preview_tools()
    assert result['status'] == 'incomplete'
    assert result['commands'][0]['exit_code'] == 1
    assert result['next_step']


def test_platform_plans_install_only_missing_tools(monkeypatch):
    monkeypatch.setattr(preview_install.shutil, 'which', lambda name: '/tools/' + name)
    commands, error = preview_install.installation_commands(['pdftoppm'], 'darwin')
    assert commands == [['/tools/brew', 'install', 'poppler']]
    commands, error = preview_install.installation_commands(['office'], 'win32')
    assert 'TheDocumentFoundation.LibreOffice' in commands[0]
    assert all('Poppler' not in arg for arg in commands[0])
    monkeypatch.setattr(preview_install.os, 'geteuid', lambda: 0, raising=False)
    commands, error = preview_install.installation_commands(['office', 'pdftoppm'], 'linux')
    assert commands[-1] == ['/tools/apt-get', 'install', '-y', 'libreoffice-impress', 'poppler-utils']
