"""How old is every number on this page?

The single rule: freshness is computed from the data's own ``fetched_at``, never from
the build clock. A page that renders ``datetime.now()`` in a "last updated" line is
claiming freshness it has not verified -- which is exactly how an earlier reporting
dashboard displayed two-month-old numbers under today's date for eight weeks without
anyone noticing.

A source is amber past twice its declared cadence and red past five times.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from ..config import cadence_days


def _age_days(stamp: str, now: dt.datetime) -> float:
    when = dt.datetime.fromisoformat(stamp)
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.UTC)
    return (now - when).total_seconds() / 86400.0


def assess(snapshot: dict[str, Any], now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.UTC)
    rows = []
    worst = "fresh"
    for name, src in sorted(snapshot.get("sources", {}).items()):
        status = src.get("status", "unknown")
        if status == "skipped":
            continue
        age = _age_days(src["fetched_at"], now)
        cadence = cadence_days(name)
        if status in {"failed"} or age > cadence * 5:
            level = "red"
        elif status == "degraded" or age > cadence * 2:
            level = "amber"
        else:
            level = "fresh"
        if level == "red" or (level == "amber" and worst != "red"):
            worst = level
        rows.append({
            "source": name,
            "status": status,
            "age_days": round(age, 1),
            "cadence_days": cadence,
            "level": level,
            "record_count": src.get("record_count", 0),
            "fetched_at": src["fetched_at"],
        })

    ok = sum(1 for r in rows if r["status"] == "ok")
    return {
        "collected_on": snapshot.get("collected_on"),
        "sources": rows,
        "ok": ok,
        "total": len(rows),
        "level": worst,
        "summary": _summary(rows, ok, snapshot.get("collected_on")),
    }


def _summary(rows: list[dict[str, Any]], ok: int, collected_on: str | None) -> str:
    bad = [r for r in rows if r["level"] != "fresh"]
    head = f"{ok} of {len(rows)} sources refreshed {collected_on}"
    if not bad:
        return head
    names = ", ".join(f"{r['source']} ({r['status']}, {r['age_days']:.0f}d)" for r in bad)
    return f"{head} — needs attention: {names}"
