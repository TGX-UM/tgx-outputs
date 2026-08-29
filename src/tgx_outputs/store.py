"""The only writer of ``data/``.

Layout (the ``data`` branch in production; a plain directory locally):

    data/snapshots/<YYYY-MM-DD>.json   whole state for one run
    data/manifests/<YYYY-MM-DD>.json   per-source status, errors, quarantine, call log
    data/latest.json                   symlink-equivalent copy of the newest snapshot

Whole state per run, not a change-only ledger. At weekly cadence a snapshot is a few
hundred kilobytes, so five years stays well inside GitHub Pages' size recommendation,
and any reader can open one file and see everything that was true that day without
replaying a diff chain.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, config_sha
from .model import Envelope, Record


def _today() -> str:
    return dt.datetime.now(dt.UTC).date().isoformat()


def snapshot_dir() -> Path:
    return DATA_DIR / "snapshots"


def manifest_dir() -> Path:
    return DATA_DIR / "manifests"


def previous_snapshot() -> dict[str, Any] | None:
    """The newest snapshot from a PREVIOUS day.

    Today's file is excluded deliberately: the guards compare against it, and a
    partial re-run would otherwise be checked against its own half-written output.
    """
    files = [p for p in sorted(snapshot_dir().glob("*.json")) if p.stem != _today()]
    if not files:
        return None
    return json.loads(files[-1].read_text())


def previous_values() -> dict[tuple[str, str, str | None], float]:
    """Flatten the last snapshot into a lookup the guards can compare against."""
    snap = previous_snapshot()
    if not snap:
        return {}
    out: dict[tuple[str, str, str | None], float] = {}
    for src in snap.get("sources", {}).values():
        for rec in src.get("records", []):
            out[(rec["metric"], rec["entity"], rec.get("period"))] = rec["value"]
    return out


def volume_history(source: str, limit: int = 7) -> list[int]:
    counts: list[int] = []
    earlier = [p for p in sorted(snapshot_dir().glob("*.json")) if p.stem != _today()]
    for path in earlier[-limit:]:
        snap = json.loads(path.read_text())
        src = snap.get("sources", {}).get(source)
        if src and src.get("status") in {"ok", "degraded"}:
            counts.append(int(src.get("record_count", 0)))
    return counts


def write_run(
    envelopes: dict[str, Envelope],
    quarantine: dict[str, list[dict[str, str]]],
    promoted: dict[str, list[Record]],
) -> tuple[Path, Path]:
    """Persist one run. Returns (snapshot_path, manifest_path)."""
    snapshot_dir().mkdir(parents=True, exist_ok=True)
    manifest_dir().mkdir(parents=True, exist_ok=True)
    stamp = _today()

    # A partial run (`--only`) must MERGE into today's snapshot rather than replace it.
    # Overwriting would silently drop every source that was not re-collected, and the
    # site would then render a page missing half its numbers with no error anywhere.
    snap_path = snapshot_dir() / f"{stamp}.json"
    man_path = manifest_dir() / f"{stamp}.json"
    snapshot: dict[str, Any] = (
        json.loads(snap_path.read_text()) if snap_path.exists()
        else {"collected_on": stamp, "config_sha": config_sha(), "sources": {}}
    )
    manifest: dict[str, Any] = (
        json.loads(man_path.read_text()) if man_path.exists()
        else {"collected_on": stamp, "config_sha": config_sha(), "sources": {}}
    )
    snapshot["config_sha"] = config_sha()
    manifest["config_sha"] = config_sha()

    # The other side of that merge: a collector deleted from the code must not survive
    # in today's file. Without this, retiring a source leaves its last records in the
    # snapshot -- and so on the page and in the freshness strip -- until the date rolls
    # over, and a push to main re-runs the refresh on the same date.
    from .collect.base import COLLECTORS

    for stale in set(snapshot["sources"]) - set(COLLECTORS):
        del snapshot["sources"][stale]
    for stale in set(manifest["sources"]) - set(COLLECTORS):
        del manifest["sources"][stale]

    for name, env in envelopes.items():
        recs = promoted.get(name, [])
        snapshot["sources"][name] = {
            "status": env.status,
            "fetched_at": env.fetched_at,
            "collector_version": env.collector_version,
            "record_count": len(recs),
            # How much of what was asked for came back, kept beside the records so the
            # freshness strip can say "current but incomplete" without re-collecting.
            "expected": env.expected,
            "found": env.found,
            "unit": env.unit,
            "records": [r.as_dict() for r in recs],
        }
        manifest["sources"][name] = {
            "status": env.status,
            "fetched_at": env.fetched_at,
            "record_count": len(recs),
            "expected": env.expected,
            "found": env.found,
            "quarantined": quarantine.get(name, []),
            "errors": env.errors,
            "calls": [{"url": c.url, "status": c.status, "ok": c.ok, "note": c.note}
                      for c in env.calls],
        }

    snap_path.write_text(json.dumps(snapshot, indent=1, sort_keys=False))
    man_path.write_text(json.dumps(manifest, indent=1, sort_keys=False))
    (DATA_DIR / "latest.json").write_text(json.dumps(snapshot, indent=1))
    return snap_path, man_path


def load_latest() -> dict[str, Any]:
    path = DATA_DIR / "latest.json"
    if not path.exists():
        raise FileNotFoundError(
            "no collected data yet -- run `tgx collect` (or `tgx collect --replay`) first"
        )
    return json.loads(path.read_text())


def load_all_manifests() -> list[dict[str, Any]]:
    return [json.loads(p.read_text()) for p in sorted(manifest_dir().glob("*.json"))]
