"""Integrity rules, applied before anything is written.

Every rule here exists because of a failure that has actually happened to a dashboard
of this kind. Each has a unit test. A record that fails a guard is quarantined -- kept
in the run manifest with its reason, but never promoted into the published series --
because the failure mode that matters is a confidently wrong number, not a missing one.
"""

from __future__ import annotations

import datetime as dt
import re
import statistics
from collections.abc import Iterable
from typing import Any

from .model import Envelope, Record

YEAR_RE = re.compile(r"^\d{4}$")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class GuardFailure(Exception):
    def __init__(self, rule: str, detail: str) -> None:
        super().__init__(f"{rule}: {detail}")
        self.rule = rule
        self.detail = detail


def _check_defined(rec: Record, semantics: dict[str, Any]) -> None:
    """A metric with no published definition does not ship."""
    if rec.metric not in semantics:
        raise GuardFailure(
            "semantics_gate",
            f"metric {rec.metric!r} has no entry in metrics.csv",
        )


def _check_schema(rec: Record, semantics: dict[str, Any]) -> None:
    spec = semantics[rec.metric]
    gran = spec.get("granularity", "none")
    if gran == "none":
        if rec.period is not None:
            raise GuardFailure(
                "schema", f"{rec.metric} is granularity:none but carries period {rec.period!r}"
            )
    else:
        if rec.period is None:
            raise GuardFailure("schema", f"{rec.metric} requires a {gran} period but has none")
        pattern = YEAR_RE if gran == "year" else MONTH_RE
        if not pattern.match(rec.period):
            raise GuardFailure("schema", f"{rec.metric} period {rec.period!r} is not a {gran}")
        # Compare the whole period, not just the year. Upstream files routinely carry
        # placeholder rows for the rest of the calendar year -- Bioconductor's stats
        # table ships zero-valued rows for every remaining month -- and a year-only
        # check lets four months of fabricated zeros through into the series.
        today = dt.datetime.now(dt.UTC).date()
        horizon = today.strftime("%Y") if gran == "year" else today.strftime("%Y-%m")
        if rec.period > horizon:
            raise GuardFailure(
                "future_period", f"{rec.metric} period {rec.period!r} is after {horizon}")


def _check_period_class(rec: Record, semantics: dict[str, Any]) -> None:
    """A cumulative counter may never be filed under a period.

    This is specdatri's Galaxy bug: five-year lifetime counters written into
    month-labelled columns, producing byte-identical consecutive rows and a headline
    total that was a sum of duplicated snapshots.
    """
    if semantics[rec.metric].get("cumulative") and rec.period is not None:
        raise GuardFailure(
            "period_class",
            f"{rec.metric} is cumulative (a level) and cannot carry period {rec.period!r}; "
            "store the level and derive deltas at query time",
        )


def _check_zero(rec: Record, previous: dict[Any, float], semantics: dict[str, Any]) -> None:
    if rec.value != 0:
        return
    if semantics[rec.metric].get("allow_zero"):
        return
    was = previous.get(rec.key())
    if was is not None and was > 0:
        raise GuardFailure(
            "no_silent_zero", f"{rec.metric}/{rec.entity} dropped {was} -> 0"
        )


def _check_monotonic(rec: Record, previous: dict[Any, float], semantics: dict[str, Any]) -> None:
    if not semantics[rec.metric].get("cumulative"):
        return
    was = previous.get(rec.key())
    if was is None or was <= 0:
        return
    if rec.value < was * 0.98:
        raise GuardFailure(
            "monotonic",
            f"cumulative {rec.metric}/{rec.entity} fell {was} -> {rec.value} (>2%)",
        )


def check_records(
    env: Envelope,
    semantics: dict[str, Any],
    previous: dict[Any, float] | None = None,
) -> tuple[list[Record], list[dict[str, str]]]:
    """Split an envelope's records into promoted and quarantined."""
    previous = previous or {}
    promoted: list[Record] = []
    quarantined: list[dict[str, str]] = []
    for rec in env.records:
        try:
            _check_defined(rec, semantics)
            # period_class runs BEFORE the generic schema check so that a cumulative
            # counter carrying a period is reported by the rule that explains it,
            # rather than as an anonymous schema violation.
            _check_period_class(rec, semantics)
            _check_schema(rec, semantics)
            _check_zero(rec, previous, semantics)
            _check_monotonic(rec, previous, semantics)
        except GuardFailure as exc:
            quarantined.append(
                {"rule": exc.rule, "metric": rec.metric, "entity": rec.entity,
                 "period": rec.period or "", "detail": exc.detail}
            )
            continue
        promoted.append(rec)
    return promoted, quarantined


def check_empty(env: Envelope) -> None:
    """HTTP 200 with zero rows is a failure, not a fact.

    A renamed graph URI, a Virtuoso mid-reload, or a filter that matches nothing all
    return a perfectly valid empty result. ``no_silent_zero`` cannot catch this,
    because nothing is written at all and the last good value is simply retained --
    the tile then looks healthy while being months out of date.
    """
    if env.status == "ok" and not env.records:
        env.degrade("returned zero records (HTTP ok but empty)")


def check_volume(env: Envelope, history: Iterable[int]) -> None:
    """A sudden collapse in record count fails the whole source."""
    counts = [c for c in history if c > 0]
    if len(counts) < 3:
        return
    median = statistics.median(counts)
    if len(env.records) < median * 0.5:
        env.fail(
            f"record count {len(env.records)} is below half the median of "
            f"recent runs ({median:.0f}); nothing promoted"
        )
