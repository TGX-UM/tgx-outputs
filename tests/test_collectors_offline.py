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

# pure_cerif is excluded: its harvest is a multi-hundred-page walk whose fixtures would
# dwarf the rest of the suite, and it is not part of the weekly refresh.
# Disabled collectors have no fixtures by design: `tgx collect --record` skips them.
# pure_cerif is excluded separately -- its harvest is hundreds of pages, and fixtures
# for it would dwarf the rest of the suite.
OFFLINE = sorted(n for n in COLLECTORS
                 if n != "pure_cerif" and _cfg.collector_enabled(n))


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
            f"{name} emits {rec.metric!r}, which has no entry in metric_semantics.yml")


@pytest.mark.parametrize("name", OFFLINE)
def test_collector_output_survives_the_guards(name, http):
    """Whatever a collector emits must be publishable, or explain why it is not."""
    env = run_one(COLLECTORS[name], http)
    promoted, dropped = guards.check_records(env, cfg.semantics(), {})
    # A little quarantine is legitimate -- OpenAlex genuinely returns a stray future
    # publication year -- but a collector that mostly produces unusable records is a bug.
    assert len(promoted) >= len(env.records) * 0.9, (
        f"{name}: {len(dropped)} of {len(env.records)} records quarantined: {dropped[:3]}")


def test_no_collector_reaches_the_network_in_replay_mode(http):
    """The offline guarantee, asserted rather than assumed."""
    assert http.mode == "replay"
    assert http._client is None, "replay mode must never open a real HTTP client"
