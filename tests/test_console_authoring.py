from __future__ import annotations

import json
import zipfile

import pytest

from framework import components, profile_authoring
from framework.paths import BUNDLED_PROFILES_ROOT, data_home
from framework.profiles import initialize_home
from framework.storage import ConflictError


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEPOISE_HOME", str(tmp_path / "home"))
    initialize_home(BUNDLED_PROFILES_ROOT)
    return data_home()


def test_full_profile_guidance_is_editable_and_revisioned(home):
    before = profile_authoring.profile_payload("personal-monochrome")
    values = {"reconstruction_guidance": {"palette_authority": "Use observed neutrals"},
              "asset_policy": {"photography": "Architectural details"},
              "visual_direction": {"custom_note": "Quiet geometric pages"}}
    profile_authoring.update_profile(before["id"], values, before["revision"])
    after = profile_authoring.profile_payload(before["id"])
    assert after["profile"]["asset_policy"] == values["asset_policy"]
    assert after["profile"]["hard_rules"] == before["profile"]["hard_rules"]
    with pytest.raises(ConflictError):
        profile_authoring.update_profile(before["id"], values, before["revision"])


def test_profile_rejects_identity_and_wrong_kind_sets(home):
    before = profile_authoring.profile_payload("personal-monochrome")
    with pytest.raises(ValueError):
        profile_authoring.update_profile(before["id"], {"profile_id": "other"}, before["revision"])
    with pytest.raises(ValueError):
        profile_authoring.update_profile(before["id"], {"library_sets": {"icons": ["consulting-core"]}}, before["revision"])


def test_inspector_reads_actual_chart_and_table(home):
    chart = components.inspect("consulting-core", "consulting-chart-doughnut-context")
    assert chart["native"]
    obj = next(obj for obj in chart["objects"] if obj["type"] == "chart")
    assert obj["chart"]["categories"] and obj["chart"]["series"][0]["values"]
    table = components.inspect("consulting-core", "consulting-table-header-orange")
    assert next(obj for obj in table["objects"] if obj["type"] == "table")["cells"]


def test_native_chart_save_updates_workbook_and_preserves_other_slides(home):
    before = components.inspect("consulting-core", "consulting-chart-column-titled")
    unrelated = components.inspect("consulting-core", "consulting-table-header-orange")["objects"]
    obj = next(obj for obj in before["objects"] if obj["type"] == "chart")
    data = obj["chart"]
    data["series"][0]["values"][0] = 123.5
    after = components.save_object("consulting-core", before["component"]["id"], obj["id"],
                                   {"chart": data, "width": obj["width"] + 2}, before["source_revision"])
    changed = next(obj for obj in after["objects"] if obj["type"] == "chart")
    assert changed["chart"]["series"][0]["values"][0] == 123.5
    assert changed["width"] == obj["width"] + 2
    assert components.inspect("consulting-core", "consulting-table-header-orange")["objects"] == unrelated
    _, _, source = components.source("consulting-core", before["component"]["id"])
    assert list((source.parent / ".history").glob("*.pptx"))
    # The chart's editable workbook also contains the replacement value.
    import io
    with zipfile.ZipFile(source) as deck:
        sheets = []
        for path in deck.namelist():
            if path.startswith("ppt/embeddings/") and path.endswith(".xlsx"):
                with zipfile.ZipFile(io.BytesIO(deck.read(path))) as workbook:
                    sheets.extend(workbook.read(name).decode() for name in workbook.namelist() if name.startswith("xl/worksheets/"))
        assert any("123.5" in sheet for sheet in sheets)
    with pytest.raises(ConflictError):
        components.save_object("consulting-core", before["component"]["id"], obj["id"], {"name": "stale"}, before["source_revision"])


def test_native_table_contents_save(home):
    before = components.inspect("consulting-core", "consulting-table-header-orange")
    obj = next(obj for obj in before["objects"] if obj["type"] == "table")
    cells = [[{"text": cell["text"]} for cell in row] for row in obj["cells"]]
    cells[0][0]["text"] = "Edited in Console"
    after = components.save_object("consulting-core", before["component"]["id"], obj["id"], {"cells": cells}, before["source_revision"])
    assert next(obj for obj in after["objects"] if obj["type"] == "table")["cells"][0][0]["text"] == "Edited in Console"


def test_grammar_is_never_mislabeled_as_native(home):
    result = components.inspect("editorial-core", "personal-archive-collage-field")
    assert result["native"] is False
    assert "objects" not in result
    before = result["catalog_revision"]
    updated = components.update_definition("editorial-core", result["component"]["id"], {"description": "A layered evidence field"}, before)
    assert updated["component"]["description"] == "A layered evidence field"
