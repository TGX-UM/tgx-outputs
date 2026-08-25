"""The guards are the reason to trust this dashboard, so they are tested first."""

import datetime as dt

from tgx_outputs import guards
from tgx_outputs.model import Envelope, Record

SEMANTICS = {
    "monthly_downloads": {"cumulative": False, "granularity": "month"},
    "yearly_outputs": {"cumulative": False, "granularity": "year"},
    "lifetime_pulls": {"cumulative": True, "granularity": "none"},
    "can_be_zero": {"cumulative": False, "granularity": "year", "allow_zero": True},
}


def env(*records):
    e = Envelope(source="test")
    e.records = list(records)
    return e


def quarantined(e, previous=None):
    _, dropped = guards.check_records(e, SEMANTICS, previous or {})
    return {d["rule"] for d in dropped}


def test_undefined_metric_never_ships():
    """A number with no published definition must not reach the page."""
    assert quarantined(env(Record("mystery_number", "x", 5))) == {"semantics_gate"}


def test_cumulative_counter_cannot_carry_a_period():
    """specdatri's Galaxy bug: a lifetime counter filed under the current month.

    It produced byte-identical consecutive rows and a headline total that was a sum of
    duplicated snapshots of the same number.
    """
    bad = Record("lifetime_pulls", "image", 5711, period="2026-08")
    assert quarantined(env(bad)) == {"period_class"}

    good = Record("lifetime_pulls", "image", 5711)
    assert quarantined(env(good)) == set()


def test_period_metric_requires_a_period():
    assert quarantined(env(Record("yearly_outputs", "all", 12))) == {"schema"}


def test_period_must_match_declared_granularity():
    assert quarantined(env(Record("monthly_downloads", "pkg", 1, period="2026"))) == {"schema"}
    assert quarantined(env(Record("yearly_outputs", "all", 1, period="2026-01"))) == {"schema"}


def test_future_months_are_rejected_not_just_future_years():
    """Bioconductor ships a zero row for every remaining month of the calendar year.

    A year-only horizon check lets those placeholders through as real measurements.
    """
    now = dt.datetime.now(dt.UTC)
    ahead = (now.replace(day=1) + dt.timedelta(days=62)).strftime("%Y-%m")
    rec = Record("monthly_downloads", "pkg", 0, period=ahead)
    assert quarantined(env(rec)) == {"future_period"}


def test_silent_zero_is_quarantined():
    prev = {("monthly_downloads", "pkg", "2026-07"): 800.0}
    rec = Record("monthly_downloads", "pkg", 0, period="2026-07")
    assert quarantined(env(rec), prev) == {"no_silent_zero"}


def test_zero_is_allowed_when_the_metric_says_so():
    prev = {("can_be_zero", "x", "2026"): 3.0}
    assert quarantined(env(Record("can_be_zero", "x", 0, period="2026")), prev) == set()


def test_cumulative_counter_going_backwards_is_quarantined():
    prev = {("lifetime_pulls", "image", None): 5711.0}
    assert quarantined(env(Record("lifetime_pulls", "image", 100)), prev) == {"monotonic"}
    # small wobble is tolerated; upstream counters are not perfectly stable
    assert quarantined(env(Record("lifetime_pulls", "image", 5700)), prev) == set()


def test_http_200_with_no_rows_degrades_the_source():
    """The failure `no_silent_zero` cannot catch: nothing is written at all."""
    e = Envelope(source="sparql")
    guards.check_empty(e)
    assert e.status == "degraded"
    assert "zero records" in e.errors[0]


def test_volume_collapse_fails_the_whole_source():
    e = env(Record("yearly_outputs", "all", 1, period="2026"))
    guards.check_volume(e, [400, 410, 405, 398])
    assert e.status == "failed"
    assert "below half the median" in e.errors[0]


def test_volume_check_stays_quiet_without_enough_history():
    e = env(Record("yearly_outputs", "all", 1, period="2026"))
    guards.check_volume(e, [400])
    assert e.status == "ok"
