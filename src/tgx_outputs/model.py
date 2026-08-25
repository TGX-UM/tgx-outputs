"""Core data types.

A collector never writes files. It returns an :class:`Envelope`, which carries both
the records and enough provenance for the site to state where every number came from
and when it was last true.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Any, Literal

Status = Literal["ok", "degraded", "failed", "skipped"]


def utcnow() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


@dataclasses.dataclass(slots=True)
class Record:
    """One measurement.

    ``period`` is the calendar period the value belongs to (``2026`` or ``2026-07``).
    A metric declared ``cumulative`` in metric_semantics.yml must leave it ``None`` --
    an all-time counter does not belong to a month, and pretending it does is how a
    dashboard ends up summing the same lifetime figure once per refresh.
    """

    metric: str
    entity: str
    value: float
    period: str | None = None
    partial: bool = False
    flags: list[str] = dataclasses.field(default_factory=list)
    extra: dict[str, Any] = dataclasses.field(default_factory=dict)

    def key(self) -> tuple[str, str, str | None]:
        return (self.metric, self.entity, self.period)

    def as_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        if not d["flags"]:
            d.pop("flags")
        if not d["extra"]:
            d.pop("extra")
        if not d["partial"]:
            d.pop("partial")
        if d["period"] is None:
            d.pop("period")
        return d


@dataclasses.dataclass(slots=True)
class Call:
    """One HTTP call, kept so the methodology page can show the literal request."""

    url: str
    status: int | None
    ok: bool
    note: str = ""


@dataclasses.dataclass(slots=True)
class Envelope:
    """What a collector returns: records plus everything needed to trust them."""

    source: str
    status: Status = "ok"
    records: list[Record] = dataclasses.field(default_factory=list)
    calls: list[Call] = dataclasses.field(default_factory=list)
    errors: list[str] = dataclasses.field(default_factory=list)
    fetched_at: str = dataclasses.field(default_factory=utcnow)
    collector_version: str = "1"

    def degrade(self, reason: str) -> None:
        """Mark the source unreliable. Never silently absorbed into 'handled'."""
        if self.status != "failed":
            self.status = "degraded"
        self.errors.append(reason)

    def fail(self, reason: str) -> None:
        self.status = "failed"
        self.errors.append(reason)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "fetched_at": self.fetched_at,
            "collector_version": self.collector_version,
            "record_count": len(self.records),
            "errors": self.errors,
            "calls": [dataclasses.asdict(c) for c in self.calls],
            "records": [r.as_dict() for r in self.records],
        }
