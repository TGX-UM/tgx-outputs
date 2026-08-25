"""The render gate and the freshness rules."""

import datetime as dt

import pytest

from tgx_outputs import config as cfg
from tgx_outputs.derive import freshness
from tgx_outputs.site import build


def _snapshot(age_days: float, status: str = "ok", records=None):
    when = dt.datetime.now(dt.UTC) - dt.timedelta(days=age_days)
    if records is None:
        records = [{"metric": "works_by_year_type", "entity": "all",
                    "value": 12.0, "period": "2026"}]
    return {
        "collected_on": when.date().isoformat(),
        "sources": {"openalex": {"status": status, "fetched_at": when.isoformat(),
                                 "record_count": len(records), "records": records}},
    }


def test_a_chart_without_a_definition_refuses_to_render(monkeypatch):
    """The render gate: no number appears unless the page can say what it counts."""
    monkeypatch.setattr(cfg, "semantics", dict)
    monkeypatch.setattr(build.cfg, "semantics", dict)
    monkeypatch.setattr(build, "CHARTS", {"works_by_year": (dict, "works_by_year_type")})
    fresh = freshness.assess(_snapshot(0))
    with pytest.raises(build.MissingDefinition):
        build.figure("works_by_year", _snapshot(0), fresh)


def test_unknown_chart_name_is_an_error_not_a_blank():
    with pytest.raises(build.MissingDefinition):
        build.figure("no_such_chart", _snapshot(0), freshness.assess(_snapshot(0)))


def test_figure_caption_carries_source_date_and_csv_link():
    snap = _snapshot(0)
    html = build.figure("works_by_year", snap, freshness.assess(snap))
    assert "Source: `openalex`" in html
    assert "collected " in html
    assert "download CSV](data/works_by_year_type.csv)" in html
    assert cfg.semantics()["works_by_year_type"]["caveat"].strip()[:40] in html


def test_freshness_is_computed_from_the_data_not_the_clock():
    assert freshness.assess(_snapshot(0))["level"] == "fresh"
    assert freshness.assess(_snapshot(20))["level"] == "amber"    # > 2x a 7-day cadence
    assert freshness.assess(_snapshot(60))["level"] == "red"      # > 5x


def test_a_degraded_source_is_never_reported_as_fresh():
    assert freshness.assess(_snapshot(0, status="degraded"))["level"] == "amber"
    assert freshness.assess(_snapshot(0, status="failed"))["level"] == "red"


def test_stale_sources_are_named_in_the_summary():
    summary = freshness.assess(_snapshot(60))["summary"]
    assert "needs attention" in summary and "openalex" in summary


def _snapshot_with(records, status="ok"):
    import datetime as _dt
    now = _dt.datetime.now(_dt.UTC)
    return {
        "collected_on": now.date().isoformat(),
        "sources": {"wikipathways": {"status": status, "fetched_at": now.isoformat(),
                                     "record_count": len(records), "records": records}},
    }


def test_a_failed_source_reads_as_missing_not_as_zero():
    """The failure that matters: a dead source rendering a confident 0.

    Summing the records of a source that returned nothing gives 0.0, and a tile then
    states "0 pathways" as fact. Missing must read as missing.
    """
    empty = _snapshot_with([], status="failed")
    assert build._value(empty, "wp_pathway_count") is None

    html = build._tiles(empty)
    assert build.MISSING in html
    assert "0 pathways" not in html


def test_a_collected_zero_is_still_shown_as_zero():
    """The converse: a real measurement of zero must not be hidden."""
    snap = _snapshot_with([{"metric": "wp_pathway_count", "entity": "WikiPathways",
                            "value": 0.0}])
    assert build._value(snap, "wp_pathway_count") == 0.0


def test_a_figure_with_no_data_is_replaced_by_an_explanation():
    empty = _snapshot_with([], status="failed")
    html = build.figure("works_by_year", empty, freshness.assess(empty))
    assert build.MISSING in html
    assert "tgx-chart" not in html, "an empty chart must not be drawn"
    assert "collection status" in html
