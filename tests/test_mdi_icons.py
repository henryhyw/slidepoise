"""Pinned MDI retrieval, Fine geometry and profile selection work together."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "slidepoise/scripts"))
sys.path.insert(0, str(ROOT / "slidepoise/runtime/src"))
import fetch_mdi_icon as mdi

BODY = '<path fill="currentColor" d="M2 2H22V22H2Z M4 4V20H20V4Z"/>'
PACKAGE = (
    {"width": 24, "height": 24, "icons": {name: {"body": BODY} for name in
        ("shield-outline", "shield", "line-symbol", "brand-outline")},
     "aliases": {"shield-alias": {"parent": "shield-outline"}}},
    {"author": {"name": "Pictogrammers"}, "license": {"spdx": "Apache-2.0", "url": "https://example.com/license"}},
    {"categories": {"Brand / Logo": ["brand-outline"]}},
)


def test_pinned_package_checks_cached_bytes_before_parsing(tmp_path, monkeypatch):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, value in zip(("icons.json", "info.json", "metadata.json"), PACKAGE):
            data = json.dumps(value).encode()
            member = tarfile.TarInfo("package/" + name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    data = buffer.getvalue()
    monkeypatch.setattr(mdi, "INTEGRITY", "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode())
    cache = tmp_path / f"mdi-{mdi.VERSION}.tgz"
    cache.write_bytes(data)
    assert mdi.load_package(tmp_path) == PACKAGE
    cache.write_bytes(data + b"changed")
    with pytest.raises(ValueError, match="checksum"):
        mdi.load_package(tmp_path)


def test_fine_retains_original_and_alias_identity(tmp_path):
    asset = mdi.fetch_icon("shield-alias", tmp_path, package=PACKAGE)
    assert asset["canonical_icon_name"] == "shield-outline"
    assert asset["requested_icon_name"] == "shield-alias"
    assert asset["asset_id"] == "mdi-shield-outline-fine"
    assert asset["geometry_treatment"]["inset_source_units"] == 0.35
    assert asset["geometry_treatment"]["id"] == "mdi-fine-v1"
    assert BODY in Path(asset["source_file"]).read_text()
    assert asset["source_sha256"] != asset["sha256"]
    assert asset["sha256"] == hashlib.sha256(Path(asset["canonical_file"]).read_bytes()).hexdigest()
    assert mdi.fetch_icon("shield-outline", tmp_path, package=PACKAGE)["sha256"] == asset["sha256"]
    assert asset["license"] == "Apache-2.0"
    assert asset["modification_notice"]


@pytest.mark.parametrize("name,options", [
    ("shield", {}), ("brand-outline", {}),
    ("shield-outline", {"line_weight": "original"}),
    ("shield-outline", {"variant": "fill"}),
])
def test_solid_brand_and_explicit_original_keep_source_geometry(tmp_path, name, options):
    asset = mdi.fetch_icon(name, tmp_path, package=PACKAGE, **options)
    assert asset["sha256"] == asset["source_sha256"]
    assert asset["canonical_file"] == asset["source_file"]
    assert asset["geometry_treatment"]["id"] == "original"
    if name == "brand-outline":
        assert asset["require_exact_identity"]
        assert not asset["treatment_recolorable"]


def test_host_can_classify_unsuffixed_line_artwork(tmp_path):
    asset = mdi.fetch_icon("line-symbol", tmp_path, package=PACKAGE, variant="line")
    assert asset["style_variant"] == "line"
    assert asset["geometry_treatment"]["line_weight"] == "fine"


@pytest.mark.parametrize("aliases", [
    {"a": {"parent": "a"}},
    {"a": {"parent": "shield-outline", "rotate": 1}},
])
def test_unsupported_aliases_are_not_silently_changed(aliases):
    with pytest.raises(ValueError):
        mdi.resolve_icon("a", {**PACKAGE[0], "aliases": aliases})


@pytest.mark.parametrize("weight", ["fine", "original"])
def test_selected_library_enables_mdi_in_legacy_config(tmp_path, weight):
    config = json.loads((ROOT / "framework/defaults/slidepoise-config.json").read_text())
    del config["remote_sources"]["mdi"]
    (tmp_path / "config.json").write_text(json.dumps(config))
    (tmp_path / "session.json").write_text(json.dumps({"profile": "consulting", "remote_sources": {"mdi": {"line_weight": weight}}}))
    result = subprocess.run([sys.executable, str(ROOT / "slidepoise/scripts/resolve_config.py"),
        "--base", str(tmp_path / "config.json"), "--profiles-root", str(ROOT / "profiles"),
        "--session", str(tmp_path / "session.json"), "--output", str(tmp_path / "resolved.json")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    resolved = json.loads((tmp_path / "resolved.json").read_text())
    assert resolved["remote_sources"]["mdi"]["enabled"] is True
    assert resolved["remote_sources"]["mdi"]["line_weight"] == weight
