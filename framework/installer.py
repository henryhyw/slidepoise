from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .paths import BUNDLED_PROFILES_ROOT, NODE_RUNTIME_PACKAGE, SKILL_ROOT, data_home, node_runtime_root
from .profiles import initialize_home
from .migration import migrate_legacy_home
from .preview_install import install_preview_tools, preview_status


def detect_host() -> dict[str, object]:
    codex_skill_dir = Path.home() / ".codex" / "skills"
    node_modules = node_runtime_root() / "node_modules"
    return {
        "python": sys.version.split()[0],
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "codex": bool(shutil.which("codex") or codex_skill_dir.is_dir()),
        "codex_skill_dir": str(codex_skill_dir),
        "node_runtime": str(node_modules),
        "preview_tools": preview_status(),
        "pptxgenjs": (node_modules / "pptxgenjs" / "package.json").is_file(),
    }


def install_codex_skill() -> str:
    target = Path.home() / ".codex" / "skills" / "slidepoise"
    target.parent.mkdir(parents=True, exist_ok=True)
    legacy = target.with_name("slidecraft")
    if legacy.exists():
        archive = data_home() / "archive" / f"legacy-skill-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy), str(archive))
    if target.exists():
        if _same_skill(target):
            return str(target)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        archive = data_home() / "archive" / f"codex-skill-{stamp}"
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(archive))
    shutil.copytree(SKILL_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    return str(target)


def _same_skill(target: Path) -> bool:
    """Avoid creating another backup when setup has no skill changes."""
    def files(root: Path) -> dict[str, bytes]:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and path.suffix != ".pyc" and path.name != ".DS_Store"
        }
    return files(SKILL_ROOT) == files(target)


def install_node_dependencies() -> bool:
    npm = shutil.which("npm")
    if not npm:
        return False
    target = node_runtime_root()
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODE_RUNTIME_PACKAGE, target / "package.json")
    completed = subprocess.run([npm, "install", "--omit=dev", "--no-audit", "--no-fund"], cwd=target,
                               capture_output=True, text=True, check=False)
    if completed.returncode:
        log = data_home() / "install-status" / "node.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text((completed.stdout or "") + (completed.stderr or ""), encoding="utf-8")
    return completed.returncode == 0


def setup(*, force_profiles: bool = False, install_skill: bool = True, install_node: bool = True, install_preview: bool = False) -> dict[str, object]:
    migration = migrate_legacy_home()
    initial_host = detect_host()
    framework_home = initialize_home(BUNDLED_PROFILES_ROOT, force=force_profiles)
    codex_skill = install_codex_skill() if install_skill and initial_host["codex"] else None
    node_dependencies = install_node_dependencies() if install_node else None
    preview = install_preview_tools() if install_preview else {"status": "not_requested", "tools": preview_status()}
    result: dict[str, object] = {
        "framework_home": framework_home,
        "host": detect_host(),
        "codex_skill": codex_skill,
        "node_dependencies": node_dependencies,
        "preview": preview,
        "migration": migration,
    }
    path = data_home() / "install.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
