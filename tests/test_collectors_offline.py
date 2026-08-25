"""Every collector, against recorded responses, with no network.

This is the test that keeps the project maintainable. A collector that only works
against the live internet cannot be changed with any confidence: you cannot tell a code
regression from an upstream outage, and CI fails for reasons nobody controls.
"""

import pytest

from tgx_outputs import config as _cfg
from tgx_outputs import config as cfg
from tgx_outputs import guards
from tgx_outputs.collect import COLLECTORS
from tgx_outputs.collect.base import run_one
from tgx_outputs.http import HttpClient

# Disabled collectors have no fixtures by design: `tgx collect --record` skips them.
OFFLINE = sorted(n for n in COLLECTORS if _cfg.collector_enabled(n))


@pytest.fixture(scope="module")
def http():
    with HttpClient(mode="replay") as client:
        yield client


@pytest.mark.parametrize("name", OFFLINE)
def test_collector_runs_and_produces_defined_metrics(name, http):
    env = run_one(COLLECTORS[name], http)
    assert env.status in {"ok", "degraded"}, f"{name} failed: {env.errors[:2]}"
    assert env.records, f"{name} produced no records"

    semantics = cfg.semantics()
    for rec in env.records:
        assert rec.metric in semantics, (
            f"{name} emits {rec.metric!r}, which has no entry in metrics.csv")


@pytest.mark.parametrize("name", OFFLINE)
def test_collector_output_survives_the_guards(name, http):
    """Whatever a collector emits must be publishable, or explain why it is not."""
    env = run_one(COLLECTORS[name], http)
    promoted, dropped = guards.check_records(env, cfg.semantics(), {})
    # A little quarantine is legitimate -- upstream genuinely ships the odd future
    # period -- but a collector that mostly produces unusable records is a bug.
    assert len(promoted) >= len(env.records) * 0.9, (
        f"{name}: {len(dropped)} of {len(env.records)} records quarantined: {dropped[:3]}")


def test_no_collector_reaches_the_network_in_replay_mode(http):
    """The offline guarantee, asserted rather than assumed."""
    assert http.mode == "replay"
    assert http._client is None, "replay mode must never open a real HTTP client"


def test_download_windows_are_never_mixed(http):
    """The bug this split fixes: a 30-day figure published as a lifetime total.

    npm and PyPI publish no lifetime counter, so ecosyste.ms answers with a rolling
    window and says so in `downloads_period`. Filing that under the all-time metric put
    "downloads, all time" under a number that was last month's, and let the project
    table add it to a genuine lifetime total.
    """
    env = run_one(COLLECTORS["ecosystems"], http)
    windows = {"package_downloads_total": "total",
               "package_downloads_recent": "last-month"}
    seen = set()
    for rec in env.records:
        if rec.metric not in windows:
            continue
        assert rec.extra["period_label"] == windows[rec.metric], (
            f"{rec.entity} reports {rec.extra['period_label']!r} but was filed under "
            f"{rec.metric}")
        assert rec.entity not in seen, f"{rec.entity} filed under two windows"
        seen.add(rec.entity)
    assert seen, "no package reported downloads at all"


def test_a_rolling_window_is_not_declared_cumulative():
    """`monotonic` guards cumulative metrics, and a rolling window legitimately falls.

    Declaring it cumulative means a quiet month is quarantined as a counter running
    backwards, and the tile silently reads "not collected" with nothing wrong upstream.
    """
    assert cfg.semantics()["package_downloads_recent"]["cumulative"] is False
    assert cfg.semantics()["package_downloads_total"]["cumulative"] is True
