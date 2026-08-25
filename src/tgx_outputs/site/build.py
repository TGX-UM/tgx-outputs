"""Turn the snapshot into the fragments MkDocs renders.

Two rules are enforced here rather than trusted to whoever writes the Markdown:

1. **A metric with no entry in metric_semantics.yml does not render.** The definition
   and the figure ship together or neither ships.
2. **Every figure carries its caption block** -- what it counts, the source, when that
   source was last collected, the caveat, and a link to the CSV behind it. A reader who
   wants to check a number should never have to ask how it was made.

Freshness comes from the data's own timestamps. ``datetime.now()`` is never used to
describe how current the page is.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .. import config as cfg
from .. import store
from ..derive import freshness, tables
from .charts import CHARTS, PALETTE, REGISTRY_NAMES
from .flow import endpoint_patterns, source_flow
from .icons import svg as icon

INCLUDES = cfg.ROOT / "includes"   # outside docs/ so MkDocs sees them as snippets, not pages


class MissingDefinition(RuntimeError):
    pass


MISSING = "not collected"


def _value(snapshot: dict[str, Any], metric: str, entity: str | None = None) -> float | None:
    """Sum a metric, or None if it was not collected.

    The distinction is the whole point. When a source fails, summing its (absent)
    records yields 0.0, and a tile then states "0 pathways" with total confidence.
    A missing number must read as missing.
    """
    recs = tables.series(snapshot, metric)
    if entity:
        recs = [r for r in recs if r["entity"] == entity]
    if not recs:
        return None
    return sum(r["value"] for r in recs)


def _fmt(value: float) -> str:
    if value >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.0f}" if value == int(value) else f"{value:,.1f}"


def figure(name: str, snapshot: dict[str, Any], fresh: dict[str, Any]) -> str:
    """One chart plus the caption block that makes it checkable."""
    if name not in CHARTS:
        raise MissingDefinition(f"no chart registered as {name!r}")
    builder, metric = CHARTS[name]
    semantics = cfg.semantics()
    if metric not in semantics:
        raise MissingDefinition(
            f"chart {name!r} renders metric {metric!r}, which has no entry in "
            "config/metric_semantics.yml -- define what it counts before showing it")
    spec = semantics[metric]
    source = spec["source"]
    row = next((r for r in fresh["sources"] if r["source"] == source), None)
    collected = row["fetched_at"][:10] if row else "unknown"
    level = row["level"] if row else "red"
    badge = {"fresh": "", "amber": " ⚠ stale", "red": " ⛔ stale"}[level]

    # The spec goes in a child <script type="application/json">, not an attribute.
    # Vega-Lite filter expressions contain single quotes (datum.entity == 'all'), which
    # silently truncate a single-quoted HTML attribute and leave a chart that renders
    # nothing. Only the literal string "</script" needs escaping here.
    if not tables.series(snapshot, metric):
        return (
            f'<div class="tgx-caption" markdown>\n'
            f'**{spec["label"]} — {MISSING}.** The `{source}` source did not return data '
            f'on the last run ({collected}), so this figure is not shown rather than '
            f'drawn from stale or partial values. '
            f'See [collection status](status.md).\n'
            f'</div>\n')

    spec_json = json.dumps(builder(), separators=(",", ":")).replace("</", "<\\/")
    return (
        f'<div class="tgx-chart">'
        f'<script type="application/json" class="tgx-spec">{spec_json}</script>'
        f'</div>\n\n'
        f'<div class="tgx-caption" markdown>\n'
        f'**{spec["label"]}.** {spec["counts"]}\n\n'
        f'{spec["caveat"].strip()}\n\n'
        f'<small>Source: `{source}` · collected {collected}{badge} · '
        f'[download CSV](data/{metric}.csv)</small>\n'
        f'</div>\n'
    )


def tile(label: str, value: str, caption: str) -> str:
    return (
        f'<div class="tgx-tile" markdown>\n'
        f'<div class="tgx-tile-label">{label}</div>\n'
        f'<div class="tgx-tile-value">{value}</div>\n'
        f'<div class="tgx-tile-caption">{caption}</div>\n'
        f'</div>\n'
    )


def _freshness_strip(fresh: dict[str, Any]) -> str:
    css = {"fresh": "tgx-fresh", "amber": "tgx-amber", "red": "tgx-red"}[fresh["level"]]
    rows = "\n".join(
        f"| `{r['source']}` | {r['status']} | {r['fetched_at'][:10]} | "
        f"{r['age_days']:.0f} d | {r['record_count']:,} |"
        for r in fresh["sources"])
    return (
        f'<div class="tgx-strip {css}">{fresh["summary"]}</div>\n\n'
        f'??? note "Per-source collection status"\n\n'
        f'    | Source | Status | Last collected | Age | Records |\n'
        f'    |---|---|---|---|---|\n'
        + "\n".join("    " + line for line in rows.splitlines()) + "\n"
    )


def _whats_new(changes: list[dict[str, Any]], semantics: dict[str, Any]) -> str:
    if not changes:
        return (
            "*Nothing to compare yet — this is the first collected snapshot. "
            "The next refresh will list what moved.*\n")
    lines = ["| What | Change |", "|---|---|"]
    for c in changes[:15]:
        label = semantics.get(c["metric"], {}).get("label", c["metric"])
        where = f"{c['entity']}" + (f" ({c['period']})" if c.get("period") else "")
        if c["kind"] == "new":
            lines.append(f"| {label} — {where} | new: {_fmt(c['to'])} |")
        else:
            sign = "+" if c["delta"] > 0 else ""
            lines.append(
                f"| {label} — {where} | {_fmt(c['from'])} → {_fmt(c['to'])} "
                f"({sign}{_fmt(c['delta'])}) |")
    return "\n".join(lines) + "\n"


def _methodology(semantics: dict[str, Any], snapshot: dict[str, Any]) -> str:
    out = []
    by_source: dict[str, list] = {}
    for name, spec in sorted(semantics.items()):
        by_source.setdefault(spec["source"], []).append((name, spec))
    for source, entries in sorted(by_source.items()):
        out.append(f"### `{source}`\n")
        for name, spec in entries:
            kind = "level (all-time)" if spec.get("cumulative") else f"per {spec['granularity']}"
            out.append(
                f'**{spec["label"]}** — `{name}`, {kind}\n\n'
                f': {spec["counts"]}\n\n'
                f': *Caveat:* {spec["caveat"].strip()}\n')
    return "\n".join(out)


def _cards(snapshot: dict[str, Any]) -> str:
    """Headline totals, one card per source.

    Registries stay separate. Bioconductor, PyPI and npm each count something different
    over a different window, so a single "downloads" card would be a large number that
    means nothing.
    """
    recs = [r for src in snapshot.get("sources", {}).values()
            for r in src.get("records", [])]

    def total(metric: str, prefix: str | None = None) -> float | None:
        hit = [r for r in recs if r["metric"] == metric
               and (prefix is None or r["entity"].startswith(prefix))]
        return sum(r["value"] for r in hit) if hit else None

    year = str(int(snapshot.get("collected_on", "2026")[:4]) - 1)
    releases = sum(r["value"] for r in recs
                   if r["metric"] == "releases_by_year" and r.get("period", "") >= year) or None

    # The registry marks say where a number comes from faster than the label does; the
    # rest are generic glyphs, because there is no logo for "a release" or "a service".
    cards = [
        ("Projects tracked", float(len(cfg.projects())), "#", "", "repo"),
        ("Releases", releases, "#releases", f"since {year}", "tag"),
        ("Bioconductor", total("package_downloads_total", "bioconductor.org/"),
         "#downloads", "downloads, all time", "r"),
        # npm and PyPI publish no lifetime counter, so these are 30-day windows and the
        # sub-label has to say so. Reading one as "all time" is how this went wrong.
        ("PyPI", total("package_downloads_recent", "pypi.org/"), "#downloads",
         "downloads, last 30 days", "python"),
        ("npm", total("package_downloads_recent", "npmjs.org/"), "#downloads",
         "downloads, last 30 days", "npm"),
        ("Docker Hub", total("docker_pulls_total"), "#containers", "pulls, all time",
         "docker"),
        ("GHCR", total("ghcr_tags"), "#containers", "tags published", "github"),
        ("Citations", total("paper_citations"), "#citations", "of these tools' papers",
         "book"),
        ("Datasets", total("dataset_downloads"), "#services", "downloads, all time",
         "database"),
        ("Services", total("services_run"), "#services", "running", "server"),
    ]

    out = ['<div class="tgx-cards">']
    for label, value, anchor, sub, glyph in cards:
        shown = MISSING if value is None else _fmt(value)
        out.append(
            f'<a class="tgx-card" href="{anchor}">'
            f'<span class="tgx-card-label">{icon(glyph)}{label}</span>'
            f'<span class="tgx-card-value">{shown}</span>'
            f'<span class="tgx-card-sub">{sub}</span></a>')
    out.append("</div>")
    return "\n".join(out) + "\n"


def _mark(proj: dict[str, Any]) -> str:
    """The letters on a tile when the project has no logo file.

    Taken from `mark:` in projects.yml where a project sets one, because initials
    derived from a name are wrong often enough to be worth overriding: molAOP is not
    "MB" and R-ODAF is not "RS". The derivation is the fallback, so a project added
    without the field still gets a tile rather than a blank square.
    """
    if proj.get("mark"):
        return str(proj["mark"])[:3]
    words = [w for w in re.split(r"[^0-9A-Za-z]+", proj["name"]) if w]
    caps = "".join(c for w in words for c in w if c.isupper())
    if len(caps) >= 2:
        return caps[:3]
    return (words[0][:2] if words else proj["id"][:2]).upper()


def _stat(value: str, label: str) -> str:
    return (f'<div class="tgx-stat"><span class="tgx-stat-value">{value}</span>'
            f'<span class="tgx-stat-label">{label}</span></div>')


def _project_tiles(snapshot: dict[str, Any]) -> str:
    """One tile per tracked project. The whole point of the page.

    This was a six-column table until 2026-08-25. A table makes ten projects look
    like ten rows of one thing and invites the reading it was built to prevent --
    scanning down a column and ranking the department's tools against each other,
    when the columns hold different registries' measures over different windows.
    A tile shows each project with its own numbers, and there is no column to run
    your eye down.

    Nothing new is collected here. Every figure on a tile was already in the table.
    """
    recs = [r for src in snapshot.get("sources", {}).values()
            for r in src.get("records", [])]

    def by(metric: str) -> list[dict[str, Any]]:
        return [r for r in recs if r["metric"] == metric]

    latest = {r["entity"]: (r.get("extra") or {}).get("date", "") for r in by("latest_release")}
    # Per registry, never summed. Bioconductor's figure is a lifetime total and npm's
    # is a rolling 30 days; one number holding their sum means nothing.
    downloads: dict[str, list[tuple[str, float, str]]] = {}
    for metric, window in (("package_downloads_total", "all time"),
                           ("package_downloads_recent", "last 30 days")):
        for r in by(metric):
            pid = (r.get("extra") or {}).get("project")
            if pid:
                registry = REGISTRY_NAMES.get(
                    (r.get("extra") or {}).get("registry", ""), r["entity"].split("/")[0])
                downloads.setdefault(pid, []).append((registry, r["value"], window))
    pulls: dict[str, float] = {}
    for r in by("docker_pulls_total"):
        pid = (r.get("extra") or {}).get("project")
        if pid:
            pulls[pid] = pulls.get(pid, 0) + r["value"]
    tags: dict[str, float] = {}
    for r in by("ghcr_tags"):
        pid = (r.get("extra") or {}).get("project")
        if pid:
            tags[pid] = tags.get(pid, 0) + r["value"]
    cites = {r["entity"]: r["value"] for r in by("paper_citations")}
    papers = {r["entity"]: (r.get("extra") or {}).get("papers", 0)
              for r in by("paper_citations")}

    cutoff = str(int(snapshot.get("collected_on", "2026")[:4]) - 1)
    recent: dict[str, float] = {}
    for r in by("releases_by_year"):
        if r.get("period", "") >= cutoff:
            recent[r["entity"]] = recent.get(r["entity"], 0) + r["value"]

    out = ['<div class="tgx-projects">']
    for i, proj in enumerate(cfg.projects()):
        pid = proj["id"]
        accent = PALETTE[i % len(PALETTE)]

        stats = []
        if pid in cites:
            n = papers.get(pid) or 0
            stats.append(_stat(_fmt(cites[pid]),
                               f"citations · {n} paper{'s' if n != 1 else ''}"))
        for registry, value, window in sorted(
                downloads.get(pid, []), key=lambda e: (e[2] != "all time", -e[1])):
            stats.append(_stat(_fmt(value), f"{registry} downloads · {window}"))
        if pulls.get(pid):
            stats.append(_stat(_fmt(pulls[pid]), "Docker Hub pulls · all time"))
        elif tags.get(pid):
            # GHCR publishes no pull count anywhere, so tags are what there is.
            stats.append(_stat(_fmt(tags[pid]), "GHCR tags published"))
        if pid in recent:
            stats.append(_stat(_fmt(recent[pid]), f"releases since {cutoff}"))
        if latest.get(pid):
            stats.append(_stat(latest[pid], "last release"))

        mark = proj.get("logo")
        chip = (f'<img class="tgx-project-logo" src="assets/images/logos/{mark}" alt="">'
                if mark else
                f'<span class="tgx-project-mark" aria-hidden="true">{_mark(proj)}</span>')

        links = []
        for svc in proj.get("services") or []:
            links.append(f'<a href="{svc["url"]}">{svc["name"]}</a>')
        for label, url in (proj.get("links") or {}).items():
            if not any(url == s.get("url") for s in proj.get("services") or []):
                links.append(f'<a href="{url}">{label}</a>')

        out.append(
            f'<article class="tgx-project" style="--tgx-project-accent: {accent}">'
            f'<div class="tgx-project-head">{chip}'
            f'<div><h3 class="tgx-project-name">{proj["name"]}</h3>'
            f'<p class="tgx-project-what">{proj["what"].strip()}</p></div></div>'
            + (f'<div class="tgx-project-stats">{"".join(stats)}</div>'
               if stats else
               '<div class="tgx-project-stats tgx-project-quiet">'
               '<div class="tgx-stat"><span class="tgx-stat-label">'
               'nothing measurable is published for this one yet</span></div></div>')
            + (f'<div class="tgx-project-foot">{" · ".join(links)}</div>' if links else "")
            + '</article>')
    out.append("</div>")

    # Four separate points, so four sentences a reader can stop after. Run together as
    # one paragraph it reads as boilerplate and gets skipped, which defeats the purpose.
    note = ("\n*A figure a tile does not show is one the project has no identifier for. "
            "It does not mean zero.*\n\n"
            "*Citations come from OpenAlex and cover every paper describing a tool, "
            "update papers included. Citing a paper is not proof the software was used, "
            "and a tool built by a community much larger than this department carries "
            "that community's citations too.*\n\n"
            "*Downloads are listed per registry with the window each one reports and are "
            "never added up: Bioconductor publishes a lifetime total, npm and PyPI a "
            "rolling 30 days.*\n\n"
            "*Containers are Docker Hub pulls where they exist and GHCR tags published "
            "where they do not, because GHCR reports no pulls at all.*\n")
    return "\n".join(out) + "\n" + note


def _latest_manifest() -> dict[str, Any]:
    files = sorted(store.manifest_dir().glob("*.json"))
    return json.loads(files[-1].read_text()) if files else {"sources": {}}


def _calls(snapshot: dict[str, Any], semantics: dict[str, Any]) -> str:
    """Every request the last run made, per source, with what it produced.

    Generated from the run manifest rather than from a hand-written list, so it cannot
    describe a call the pipeline no longer makes. A source that asked for nothing says
    so instead of being left out.
    """
    manifest = _latest_manifest()
    out: list[str] = []

    for name in sorted(manifest.get("sources", {})):
        src = manifest["sources"][name]
        calls = src.get("calls") or []
        snap_src = snapshot.get("sources", {}).get(name, {})

        metrics: dict[str, int] = {}
        for rec in snap_src.get("records", []):
            metrics[rec["metric"]] = metrics.get(rec["metric"], 0) + 1

        status = src.get("status", "unknown")
        when = (src.get("fetched_at") or "")[:10]
        # A disabled collector makes no calls, so it has nothing to explain here. That
        # it exists and is switched off is a fact about the configuration, and the
        # collection status page is where configuration belongs.
        if status == "skipped":
            continue

        out.append(f"### `{name}` {{ #{name} }}\n")

        out.append(
            f"{len(calls)} request{'s' if len(calls) != 1 else ''} on {when}, "
            f"status `{status}`, {src.get('record_count', 0):,} records kept.\n")
        out.append(source_flow(
            name, endpoint_patterns([c["url"] for c in calls]),
            sorted(metrics.items()), src.get("record_count", 0)) + "\n")

        if calls:
            out.append('??? note "Every request, in the order it was made"\n')
            out.append("    | # | URL | What came back |")
            out.append("    |---|---|---|")
            for i, call in enumerate(calls, 1):
                url = call["url"].replace("|", "%7C")
                note = call.get("note") or ""
                mark = "" if call.get("ok") else " ⛔"
                out.append(f"    | {i} | `{url}` | {note}{mark} |")
            out.append("")

        for err in src.get("errors", [])[:3]:
            out.append(f"!!! warning \"Reported a problem\"\n\n    {err.splitlines()[0]}\n")
        quarantined = src.get("quarantined") or []
        if quarantined:
            rules = {q["rule"] for q in quarantined}
            out.append(
                f"{len(quarantined)} record(s) were quarantined by "
                f"{', '.join(f'`{r}`' for r in sorted(rules))} and are in the run "
                f"manifest rather than on the page.\n")

    return "\n".join(out) + "\n"


def build() -> int:
    snapshot = store.load_latest()
    semantics = cfg.semantics()
    INCLUDES.mkdir(parents=True, exist_ok=True)

    fresh = freshness.assess(snapshot)
    changes_path = cfg.DATA_DIR / "derived" / "whats_new.json"
    changes = json.loads(changes_path.read_text()) if changes_path.exists() else []

    fragments = {
        "freshness.md": _freshness_strip(fresh),
        "cards.md": _cards(snapshot),
        "projects.md": _project_tiles(snapshot),
        "whats_new.md": _whats_new(changes, semantics),
        "methodology.md": _methodology(semantics, snapshot),
        "calls.md": _calls(snapshot, semantics),
    }
    for name in CHARTS:
        fragments[f"fig_{name}.md"] = figure(name, snapshot, fresh)

    for name, text in fragments.items():
        (INCLUDES / name).write_text(text)

    print(f"  {len(fragments)} fragments → {INCLUDES.relative_to(cfg.ROOT)}")
    print(f"  freshness level: {fresh['level']}")
    if fresh["level"] == "red":
        print("  ⛔ at least one source is badly stale; the page will say so")
    return 0
