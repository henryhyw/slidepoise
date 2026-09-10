import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile


def test_sdist_builds_self_contained_wheel_and_runs_outside_repository(tmp_path):
    source = Path(__file__).resolve().parents[1]
    build = tmp_path / "source"
    build.mkdir()
    for name in ("setup.py", "pyproject.toml", "MANIFEST.in", "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md"):
        shutil.copy2(source / name, build / name)
    for name in ("framework", "webapp", "slidepoise", "profiles", "library-sets"):
        shutil.copytree(source / name, build / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    def command(arguments, cwd, env=None):
        return subprocess.run([sys.executable, *arguments], cwd=cwd, env=env, text=True, capture_output=True, check=True)
    command(["-m", "build", "--sdist"], build)
    extracted = tmp_path / "sdist"
    extracted.mkdir()
    with tarfile.open(next((build / "dist").glob("*.tar.gz"))) as archive:
        if sys.version_info >= (3, 12):
            archive.extractall(extracted, filter="data")
        else:
            root = extracted.resolve()
            for member in archive.getmembers():
                destination = (extracted / member.name).resolve()
                assert destination == root or root in destination.parents
            archive.extractall(extracted)
    root = next(extracted.iterdir())
    command(["-m", "build", "--wheel"], root)
    installed = tmp_path / "installed"
    installed.mkdir()
    with zipfile.ZipFile(next((root / "dist").glob("*.whl"))) as wheel:
        names = wheel.namelist()
        for path in ("slidepoise/SKILL.md", "profiles/consulting/profile.json", "library-sets/catalog.json"):
            assert "framework/_bundled/" + path in names
        assert "webapp/ui/session-panel.js" in names
        assert "webapp/console/index.html" in names
        assert wheel.read("webapp/console/mark.svg") == (source / "webapp/console/mark.svg").read_bytes()
        assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
        assert not any("__pycache__" in name for name in names)
        wheel.extractall(installed)
    environment = {**os.environ, "PYTHONPATH": str(installed), "SLIDEPOISE_HOME": str(tmp_path / "home")}
    outside = tmp_path / "user-project"
    outside.mkdir()
    command(["-m", "framework.cli", "setup", "--skip-skill", "--skip-node"], outside, environment)
    result = command(["-m", "framework.cli", "run", "create", "Packaged", "--location", "presentation"], outside, environment)
    run = json.loads(result.stdout)["path"]
    command(["-m", "framework.cli", "run", "resolve", run], outside, environment)
    assert Path(run).parent == outside.resolve()
    assert json.loads((Path(run) / "work/resolved-config.json").read_text())["library_sets"]["records"]
