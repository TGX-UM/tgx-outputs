"""What changed since the previous run.

The only panel people come back for. It is a plain diff of two consecutive snapshots:
new entities, and metrics that moved. Deliberately dumb -- if it cannot explain a
change from the two files alone, it does not report one.
"""

from __future__ import annotations

from typing import Any

INTERESTING = {
    "releases_by_year",
    "works_by_year_type",
    "zenodo_by_year_type",
    "rsd_mentions",
    "package_downloads_total",
}


def _flatten(snapshot: dict[str, Any]) -> dict[tuple[str, str, str | None], float]:
    out: dict[tuple[str, str, str | None], float] = {}
    for src in snapshot.get("sources", {}).values():
        for rec in src.get("records", []):
            out[(rec["metric"], rec["entity"], rec.get("period"))] = rec["value"]
    return out


def diff(current: dict[str, Any], previous: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not previous:
        return []
    now, before = _flatten(current), _flatten(previous)
    changes: list[dict[str, Any]] = []
    for key, value in now.items():
        metric, entity, period = key
        if metric not in INTERESTING:
            continue
        was = before.get(key)
        if was is None:
            changes.append({"metric": metric, "entity": entity, "period": period,
                            "kind": "new", "from": None, "to": value})
        elif value != was:
            changes.append({"metric": metric, "entity": entity, "period": period,
                            "kind": "changed", "from": was, "to": value,
                            "delta": round(value - was, 2)})
    changes.sort(key=lambda c: abs(c.get("delta") or c["to"] or 0), reverse=True)
    return changes[:40]
