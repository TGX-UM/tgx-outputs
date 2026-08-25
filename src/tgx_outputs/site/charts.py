"""Vega-Lite specs.

Specs are written as plain dicts and point at the CSV the page also offers for
download, so the chart and the download link cannot disagree: they are the same file.

Colours come from a small palette that keeps its contrast in both light and dark mode,
and every spec sets an explicit background of ``transparent`` so it inherits the page
rather than punching a white rectangle into a dark theme.
"""

from __future__ import annotations

from typing import Any

# The first two are the department's own logo colours, so a chart on this page is
# recognisably from the same family as the mark in the header. The rest extend the
# range. All six read acceptably in light and dark and stay distinguishable in
# greyscale print, which rules out putting the navy in here: at chart weight it is
# indistinguishable from the axis furniture.
PALETTE = ["#00a2db", "#e84e10", "#4a8a72", "#8a5fa8", "#a8484f", "#6b7c93"]

BASE: dict[str, Any] = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "background": "transparent",
    "width": "container",
    "height": 260,
    # Without this, the width we set is the plotting area and the axis labels are drawn
    # outside it, so every figure overflows its column by the width of the y-axis.
    "autosize": {"type": "fit", "contains": "padding"},
    "config": {
        "axis": {"labelColor": "#8a8f98", "titleColor": "#8a8f98",
                 "gridColor": "#8a8f9833", "domainColor": "#8a8f9855",
                 "tickColor": "#8a8f9855"},
        "legend": {"labelColor": "#8a8f98", "titleColor": "#8a8f98"},
        "view": {"stroke": "transparent"},
        "range": {"category": PALETTE},
    },
}


def _spec(mark: dict[str, Any], encoding: dict[str, Any], csv: str,
          transform: list | None = None, **over: Any) -> dict[str, Any]:
    # `csv` is relative to the SITE ROOT. charts.js rewrites it to an absolute URL
    # at render time, because the correct number of "../" hops differs between the
    # index page and a sub-page, and differs again under a GitHub Pages project path.
    spec = {**BASE, "data": {"url": csv, "format": {"type": "csv"}},
            "mark": mark, "encoding": encoding}
    if transform:
        spec["transform"] = transform
    spec.update(over)
    return spec


def bioc_ips() -> dict[str, Any]:
    return _spec(
        {"type": "line", "tooltip": True, "point": False},
        {"x": {"field": "period", "type": "temporal", "title": None},
         "y": {"field": "value", "type": "quantitative", "title": "Distinct IPs / month"},
         "color": {"field": "entity", "type": "nominal", "title": "Package"}},
        "data/bioc_distinct_ips_monthly.csv",
        # The in-progress month is always incomplete and would read as a cliff.
        transform=[{"filter": "datum.partial != 'true'"}],
        height=280,
    )


def releases_by_year() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"x": {"field": "period", "type": "ordinal", "title": "Year"},
         "y": {"field": "value", "type": "quantitative", "title": "Releases and tags"}},
        "data/releases_by_year.csv",
        transform=[{"filter": "datum.period >= '2012'"}],
    )


def rsd_mentions() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"y": {"field": "entity", "type": "nominal", "sort": "-x", "title": None},
         "x": {"field": "value", "type": "quantitative", "title": "Papers mentioning",
               "scale": {"type": "sqrt"}},
         "color": {"field": "entity", "type": "nominal", "legend": None}},
        "data/rsd_mentions.csv",
        height=320,
    )


def docker_pulls() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"y": {"field": "entity", "type": "nominal", "sort": "-x", "title": None},
         "x": {"field": "value", "type": "quantitative", "title": "Pulls, all time"},
         "color": {"field": "entity", "type": "nominal", "legend": None}},
        "data/docker_pulls_total.csv",
        height=280,
    )


def ghcr_tags() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"y": {"field": "entity", "type": "nominal", "sort": "-x", "title": None},
         "x": {"field": "value", "type": "quantitative", "title": "Tags published"},
         "color": {"field": "entity", "type": "nominal", "legend": None}},
        "data/ghcr_tags.csv",
        height=280,
    )


def dataset_downloads() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"y": {"field": "entity", "type": "nominal", "sort": "-x", "title": None},
         "x": {"field": "value", "type": "quantitative", "title": "Unique downloads"},
         "color": {"field": "entity", "type": "nominal", "legend": None}},
        "data/dataset_downloads.csv",
        height=140,
    )


def citations() -> dict[str, Any]:
    return _spec(
        {"type": "bar", "tooltip": True},
        {"y": {"field": "entity", "type": "nominal", "sort": "-x", "title": None},
         "x": {"field": "value", "type": "quantitative", "title": "Citations"},
         "color": {"field": "entity", "type": "nominal", "legend": None}},
        "data/paper_citations.csv",
        height=280,
    )


CHARTS = {
    "bioc_ips": (bioc_ips, "bioc_distinct_ips_monthly"),
    "releases_by_year": (releases_by_year, "releases_by_year"),
    "rsd_mentions": (rsd_mentions, "rsd_mentions"),
    "citations": (citations, "paper_citations"),
    "docker_pulls": (docker_pulls, "docker_pulls_total"),
    "ghcr_tags": (ghcr_tags, "ghcr_tags"),
    "dataset_downloads": (dataset_downloads, "dataset_downloads"),
}
