from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


ROOT = Path(__file__).resolve().parent


class build_py(_build_py):
    """Place the self-contained skill and profiles inside the wheel."""

    def run(self) -> None:
        super().run()
        bundle = Path(self.build_lib) / "framework" / "_bundled"
        for name in ("slidepoise", "profiles", "library-sets"):
            target = bundle / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(
                ROOT / name,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "work", "deliverables"),
            )


setup(cmdclass={"build_py": build_py})
