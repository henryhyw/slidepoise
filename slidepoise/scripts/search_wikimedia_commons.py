#!/usr/bin/env python3
"""Search Wikimedia Commons for host-Agent reviewable media candidates."""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(str((value or {}).get("value") or ""))).strip()


def request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "SlidePoise/0.4 (remote media retrieval)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def source_enabled(config: Path) -> None:
    payload = json.loads(config.read_text(encoding="utf-8"))
    if not bool(((payload.get("remote_sources") or {}).get("wikimedia_commons") or {}).get("enabled")):
        raise SystemExit("Wikimedia Commons retrieval is disabled in the resolved config")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_enabled(args.config)
    limit = max(1, min(20, args.limit))
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": args.query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "format": "json",
        "formatversion": "2",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    payload = request_json(url)
    candidates = []
    for page in (payload.get("query") or {}).get("pages", []) or []:
        info = ((page.get("imageinfo") or [{}])[0])
        metadata = info.get("extmetadata") or {}
        candidates.append({
            "file_title": page.get("title"),
            "description_url": info.get("descriptionurl"),
            "original_url": info.get("url"),
            "mime": info.get("mime"),
            "width": info.get("width"),
            "height": info.get("height"),
            "artist": clean(metadata.get("Artist")),
            "credit": clean(metadata.get("Credit")),
            "license_short_name": clean(metadata.get("LicenseShortName")),
            "license_url": clean(metadata.get("LicenseUrl")),
            "usage_terms": clean(metadata.get("UsageTerms")),
            "attribution_required": clean(metadata.get("AttributionRequired")),
            "selection_status": "candidate_pending_host_identity_license_and_visual_review",
        })
    result = {
        "provider": "Wikimedia Commons",
        "query": args.query,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "notice": "Search results are candidates only. The host Agent must inspect the exact file page, verify identity and licensing, and select the asset.",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
