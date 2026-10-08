"""Console access to the same indexed reference recall used by the Agent."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from .paths import SKILL_ROOT
from .profiles import library_catalog

sys.path.insert(0, str(SKILL_ROOT / "runtime/src"))
from slidepoise.reference_retrieval import build_index, load_records, query_index


def search(profile_id: str, query: str, authenticity: str = "authentic") -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 1200:
        raise ValueError("Describe the slide's message or visual relationship in up to 1,200 characters")
    catalog, _ = library_catalog(profile_id, "visual_references")
    records, _ = load_records([catalog])
    # Build from current catalog and source files so Console edits apply immediately.
    with tempfile.TemporaryDirectory(prefix="slidepoise-reference-search-") as directory:
        index = Path(directory) / "references.sqlite"
        build_index(records, index)
        result = query_index(index, {"communication_job": query}, authenticity=authenticity, limit=24)
    return {**result, "profile_id": profile_id, "selection_owner": "host_agent"}
