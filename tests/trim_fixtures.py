#!/usr/bin/env python3
"""Shrink recorded HTTP fixtures so they can live in git.

`tgx collect --record` saves whatever the upstream API actually returned, which for
Bioconductor is a 12 MB statistics table covering every package it has ever hosted.
Committing that would put the repository into the tens of megabytes and make every
checkout slow, for no test value: the offline suite needs a response with the right
*shape*, not the whole world.

This trims the large ones in place, keeping the rows that matter, and leaves the small
ones untouched. Fixture filenames are hashes of the request, so trimming the body does
not change which request a fixture answers.

Run via `make fixtures` after re-recording. It lives beside the fixtures it maintains
rather than in a scripts/ directory of its own, which held nothing else.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
KEEP_PACKAGES = {"rWikiPathways", "BridgeDbR", "RCy3"}
MAX_TSV_ROWS = 400
MAX_JSON_BYTES = 120_000


def trim_tsv(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or "\t" not in lines[0]:
        return None
    header = lines[0]
    cols = header.split("\t")
    if "Package" not in cols:
        return None
    idx = cols.index("Package")
    kept = [ln for ln in lines[1:] if ln.split("\t")[idx] in KEEP_PACKAGES]
    # Keep a slice of everything else too, so rank-style calculations still have a
    # population to work against rather than a table of three rows.
    others = [ln for ln in lines[1:] if ln.split("\t")[idx] not in KEEP_PACKAGES]
    kept += others[: max(0, MAX_TSV_ROWS - len(kept))]
    return "\n".join([header, *kept]) + "\n"


def trim_json(text: str) -> str | None:
    try:
        data = json.loads(text)
    except ValueError:
        return None
    for key in ("results", "hits"):
        if isinstance(data, dict) and key in data:
            node = data[key]
            if isinstance(node, dict) and "hits" in node:
                node["hits"] = node["hits"][:5]
            elif isinstance(node, list):
                data[key] = node[:5]
            return json.dumps(data)
    if isinstance(data, list):
        # ecosyste.ms returns one verbose object per package; a handful is plenty to
        # prove the parsing works, and twenty of them is over a megabyte.
        return json.dumps(data[:4])
    return None


def main() -> int:
    if not FIXTURES.exists():
        print("no fixtures directory; run `tgx collect --record` first")
        return 1
    before = after = 0
    for path in sorted(FIXTURES.glob("*.json")):
        raw = path.read_text()
        before += len(raw)
        blob = json.loads(raw)
        body = blob.get("text", "")
        if len(raw) <= MAX_JSON_BYTES:
            after += len(raw)
            continue
        new = trim_tsv(body) or trim_json(body)
        if new is None:
            print(f"  ! {path.name}: {len(raw):,} bytes, no trimmer matched")
            after += len(raw)
            continue
        blob["text"] = new
        blob["_trimmed"] = "reduced for the offline test suite; not a full response"
        out = json.dumps(blob, indent=1)
        path.write_text(out)
        after += len(out)
        print(f"  trimmed {path.name}: {len(raw):,} → {len(out):,} bytes")
    print(f"\n  fixtures: {before/1e6:.1f} MB → {after/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
