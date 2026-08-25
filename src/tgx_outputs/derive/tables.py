"""Everything the site renders, as CSV.

Every figure on the page links to the CSV behind it. That is not a convenience
feature: it is what lets a sceptical reader check a number instead of trusting it,
and it means the department keeps a usable dataset even if the site itself is
abandoned.

Long format (``metric,entity,period,value,partial``), never a wide matrix with one
column per package. A wide matrix rewrites its own header whenever a package is added
or removed, which makes the file history unreadable and the diffs meaningless.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

FIELDS = ["metric", "entity", "period", "value", "partial", "collected_on"]


def write_long(snapshot: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    """One CSV per metric, plus a combined `all_metrics.csv`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    collected = snapshot.get("collected_on", "")
    by_metric: dict[str, list[dict[str, Any]]] = {}

    for src in snapshot.get("sources", {}).values():
        for rec in src.get("records", []):
            row = {
                "metric": rec["metric"],
                "entity": rec["entity"],
                "period": rec.get("period") or "",
                "value": rec["value"],
                "partial": "true" if rec.get("partial") else "",
                "collected_on": collected,
            }
            by_metric.setdefault(rec["metric"], []).append(row)

    written: dict[str, Path] = {}
    combined: list[dict[str, Any]] = []
    for metric, rows in sorted(by_metric.items()):
        rows.sort(key=lambda r: (r["period"], r["entity"]))
        path = out_dir / f"{metric}.csv"
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        written[metric] = path
        combined.extend(rows)

    if combined:
        combined.sort(key=lambda r: (r["metric"], r["period"], r["entity"]))
        path = out_dir / "all_metrics.csv"
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(combined)
        written["_all"] = path
    return written


def series(snapshot: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    """All records for one metric, ready to hand to a chart spec."""
    out = []
    for src in snapshot.get("sources", {}).values():
        for rec in src.get("records", []):
            if rec["metric"] == metric:
                out.append(rec)
    out.sort(key=lambda r: (r.get("period") or "", r["entity"]))
    return out


def totals(snapshot: dict[str, Any], metric: str) -> float:
    return sum(r["value"] for r in series(snapshot, metric))
