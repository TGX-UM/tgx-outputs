"""The render gate and the freshness rules."""

import datetime as dt
import json

import pytest

from tgx_outputs import config as cfg
from tgx_outputs.derive import freshness
from tgx_outputs.site import build


def _snapshot(age_days: float, status: str = "ok", records=None):
    when = dt.datetime.now(dt.UTC) - dt.timedelta(days=age_days)
    if records is None:
        records = [{"metric": "releases_by_year", "entity": "bridgedb",
                    "value": 12.0, "period": "2026"}]
    return {
        "collected_on": when.date().isoformat(),
        "sources": {"github": {"status": status, "fetched_at": when.isoformat(),
                               "record_count": len(records), "records": records}},
    }


def test_a_chart_without_a_definition_refuses_to_render(monkeypatch):
    """The render gate: no number appears unless the page can say what it counts."""
    monkeypatch.setattr(cfg, "semantics", dict)
    monkeypatch.setattr(build.cfg, "semantics", dict)
    monkeypatch.setattr(build, "CHARTS", {"releases_by_year": (dict, "releases_by_year")})
    fresh = freshness.assess(_snapshot(0))
    with pytest.raises(build.MissingDefinition):
        build.figure("releases_by_year", _snapshot(0), fresh)


def test_unknown_chart_name_is_an_error_not_a_blank():
    with pytest.raises(build.MissingDefinition):
        build.figure("no_such_chart", _snapshot(0), freshness.assess(_snapshot(0)))


def test_figure_caption_carries_source_date_and_csv_link():
    snap = _snapshot(0)
    html = build.figure("releases_by_year", snap, freshness.assess(snap))
    assert "Source: `github`" in html
    assert "collected " in html
    assert "download CSV](data/releases_by_year.csv)" in html
    assert cfg.semantics()["releases_by_year"]["caveat"].strip()[:40] in html


def test_freshness_is_computed_from_the_data_not_the_clock():
    assert freshness.assess(_snapshot(0))["level"] == "fresh"
    assert freshness.assess(_snapshot(20))["level"] == "amber"    # > 2x a 7-day cadence
    assert freshness.assess(_snapshot(60))["level"] == "red"      # > 5x


def test_a_degraded_source_is_never_reported_as_fresh():
    assert freshness.assess(_snapshot(0, status="degraded"))["level"] == "amber"
    assert freshness.assess(_snapshot(0, status="failed"))["level"] == "red"


def test_stale_sources_are_named_in_the_summary():
    summary = freshness.assess(_snapshot(60))["summary"]
    assert "needs attention" in summary and "github" in summary


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
    assert build._value(empty, "rsd_mentions") is None

    html = build._cards(empty)
    assert build.MISSING in html
    # the failure mode: a dead source rendering a confident zero
    assert ">0<" not in html


def test_a_collected_zero_is_still_shown_as_zero():
    """The converse: a real measurement of zero must not be hidden."""
    snap = _snapshot_with([{"metric": "rsd_mentions", "entity": "Some Tool",
                            "value": 0.0}])
    assert build._value(snap, "rsd_mentions") == 0.0


def test_a_figure_with_no_data_is_replaced_by_an_explanation():
    empty = _snapshot_with([], status="failed")
    html = build.figure("releases_by_year", empty, freshness.assess(empty))
    assert build.MISSING in html
    assert "tgx-chart" not in html, "an empty chart must not be drawn"
    assert "collection status" in html


def test_retiring_a_metric_removes_its_csv(tmp_path):
    """A stale CSV is a number that stopped being collected with nothing to say so."""
    from tgx_outputs.derive import tables

    (tmp_path / "old_metric.csv").write_text("metric,entity,period,value\n")
    snap = _snapshot(0)
    tables.write_long(snap, tmp_path)
    assert not (tmp_path / "old_metric.csv").exists()
    assert (tmp_path / "releases_by_year.csv").exists()


def test_retiring_a_collector_removes_it_from_todays_snapshot(tmp_path, monkeypatch):
    """The counterpart to retiring a metric: the source itself has to go too.

    A partial run merges into today's snapshot, so a deleted collector would otherwise
    keep its last records -- and its row in the freshness strip -- until midnight.
    """
    from tgx_outputs import store
    from tgx_outputs.model import Envelope

    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    stamp = store._today()
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "snapshots" / f"{stamp}.json").write_text(json.dumps({
        "collected_on": stamp,
        "sources": {"retired_source": {"status": "ok", "fetched_at": stamp,
                                       "record_count": 1, "records": [{}]}},
    }))

    env = Envelope(source="github")
    store.write_run({"github": env}, {}, {"github": []})

    snap = json.loads((tmp_path / "snapshots" / f"{stamp}.json").read_text())
    assert "retired_source" not in snap["sources"]
    assert "github" in snap["sources"]


def test_every_overview_card_carries_an_icon():
    """A mistyped glyph key renders nothing at all, which is invisible in review."""
    html = build._cards(_snapshot_with([]))
    assert html.count('class="tgx-card"') == 10
    assert html.count('class="tgx-icon"') == html.count('class="tgx-card"')


def test_icons_are_self_contained_markup():
    from tgx_outputs.site import icons

    for name in icons._ICONS:
        markup = icons.svg(name)
        assert markup.startswith("<svg") and markup.endswith("</svg>")
        # No external reference of any kind: the page must render with no network.
        assert "http" not in markup and "url(" not in markup
    assert icons.svg("no-such-icon") == ""


def test_endpoint_patterns_collapse_repeated_shapes():
    """Nineteen calls to one endpoint are one row marked x19, not nineteen rows."""
    from tgx_outputs.site.flow import endpoint_patterns

    same = ["https://api.github.com/graphql (a/b)"] * 19
    assert endpoint_patterns(same) == [("api.github.com/graphql", 19)]

    varied = [
        "https://packages.ecosyste.ms/api/v1/registries/npmjs.org/packages/bridgedb",
        "https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pybacting",
    ]
    pattern, count = endpoint_patterns(varied)[0]
    assert count == 2
    assert pattern == "packages.ecosyste.ms/api/v1/registries/…/packages/…"
    assert "bridgedb" not in pattern, "a varying segment must not leak one call's value"


def test_the_calls_page_lists_every_request_that_was_made(monkeypatch):
    """The explainability promise: every URL asked for is on the page, in full."""
    manifest = {"sources": {"github": {
        "status": "ok", "fetched_at": "2026-08-25T00:00:00+00:00", "record_count": 2,
        "calls": [
            {"url": "https://api.github.com/graphql (bridgedb/BridgeDb)",
             "status": 200, "ok": True, "note": "pushed 2026-08-02"},
            {"url": "https://api.github.com/graphql (cdk/cdk)",
             "status": 200, "ok": True, "note": "pushed 2026-08-18"},
        ],
        "errors": [], "quarantined": []}}}
    monkeypatch.setattr(build, "_latest_manifest", lambda: manifest)

    snap = _snapshot(0)
    snap["sources"] = {"github": {"status": "ok", "fetched_at": "2026-08-25T00:00:00+00:00",
                                  "record_count": 2, "records": [
                                      {"metric": "releases_by_year", "entity": "cdk",
                                       "value": 1.0, "period": "2026"}]}}
    html = build._calls(snap, cfg.semantics())

    for call in manifest["sources"]["github"]["calls"]:
        assert call["url"] in html, "a call was made and not published"
    assert "releases_by_year" in html, "the metrics a source produced must be shown"
    assert "tgx-flow" in html


def test_a_disabled_source_is_shown_as_disabled_rather_than_omitted(monkeypatch):
    """A source that is off should be visible. Silence looks the same as an oversight."""
    monkeypatch.setattr(build, "_latest_manifest", lambda: {"sources": {"wikipathways": {
        "status": "skipped", "fetched_at": "2026-08-25T00:00:00+00:00",
        "record_count": 0, "calls": [], "errors": [], "quarantined": []}}})
    html = build._calls(_snapshot(0), cfg.semantics())
    assert "wikipathways" in html
    assert "no calls" in html or "made no calls" in html
