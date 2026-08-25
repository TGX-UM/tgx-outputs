"""One diagram per source: what it asked for, and what came back.

Drawn as inline SVG rather than with a diagramming library. Mermaid would mean
shipping another megabyte of JavaScript to render boxes and arrows, and this page has
to keep the property the rest of the site has: nothing is fetched from anywhere at
render time, and the whole thing archives in one piece.

Nothing here is styled inline. Every element carries a class and the colours live in
``extra.css``, which is what lets the same markup work in light and dark mode without
the build knowing which one a reader is in.

The endpoints on the left are patterns, not individual calls. A collector that asks
about nineteen repositories makes nineteen requests to one endpoint, and nineteen
identical boxes would say less than one box marked "x19". The literal URL of every
call is listed in the table underneath, which is where completeness belongs.
"""

from __future__ import annotations

import html
from urllib.parse import urlsplit

BOX_H = 26
GAP = 8
PAD = 10
COL_W = 250          # endpoint column
MID_W = 130          # collector column
RIGHT_W = 200        # metric column
WIDTH = COL_W + MID_W + RIGHT_W + 2 * PAD


def endpoint_patterns(urls: list[str]) -> list[tuple[str, int]]:
    """Collapse a list of URLs into the distinct shapes that were requested.

    Segments that are the same across every call to a host are kept; a segment that
    varies becomes an ellipsis. So nineteen GraphQL posts collapse to one
    ``api.github.com/graphql``, and the per-package lookups to
    ``packages.ecosyste.ms/api/v1/registries/…/packages/…``.
    """
    by_host: dict[str, list[list[str]]] = {}
    order: list[str] = []
    for url in urls:
        parts = urlsplit(url.split(" ")[0])   # github logs "url (owner/name)"
        host = parts.netloc
        if host not in by_host:
            by_host[host] = []
            order.append(host)
        by_host[host].append([s for s in parts.path.split("/") if s])

    out: list[tuple[str, int]] = []
    for host in order:
        paths = by_host[host]
        depth = max(len(p) for p in paths)
        merged: list[str] = []
        for i in range(depth):
            values = {tuple(p[i : i + 1]) for p in paths}
            merged.append(paths[0][i] if len(values) == 1 and len(paths[0]) > i else "…")
        out.append(("/".join([host, *merged]), len(paths)))
    return out


def _box(x: int, y: int, w: int, label: str, cls: str, sub: str = "") -> str:
    text = html.escape(_ellipsis(label, int(w / 6.2)))
    inner = (
        f'<text x="{x + 8}" y="{y + 17}" class="tgx-flow-label">{text}</text>'
        if not sub
        else (f'<text x="{x + 8}" y="{y + 12}" class="tgx-flow-label">{text}</text>'
              f'<text x="{x + 8}" y="{y + 23}" class="tgx-flow-sub">{html.escape(sub)}</text>')
    )
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{BOX_H}" rx="4" class="{cls}"/>'
            + inner)


def _ellipsis(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    mid = (x1 + x2) / 2
    return (f'<path d="M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}" '
            f'class="tgx-flow-line" marker-end="url(#tgx-arrow)"/>')


def source_flow(source: str, endpoints: list[tuple[str, int]],
                metrics: list[tuple[str, int]], records: int) -> str:
    """Endpoints on the left, the collector in the middle, metrics on the right."""
    rows = max(len(endpoints), len(metrics), 1)
    height = rows * (BOX_H + GAP) + GAP + 20
    mid_y = height / 2 - BOX_H / 2

    parts = [
        f'<svg class="tgx-flow" viewBox="0 0 {WIDTH} {height}" width="100%" '
        f'height="{height}" role="img" '
        f'aria-label="What the {html.escape(source)} collector requests, and the '
        f'metrics it produces">',
        '<defs><marker id="tgx-arrow" viewBox="0 0 8 8" refX="7" refY="4" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M0,0 L8,4 L0,8 z" class="tgx-flow-head"/></marker></defs>',
    ]

    mid_x = PAD + COL_W + 20
    parts.append(_box(mid_x, int(mid_y), MID_W - 40, source, "tgx-flow-node",
                      f"{records:,} records"))

    for i, (pattern, count) in enumerate(endpoints):
        y = GAP + i * (BOX_H + GAP)
        parts.append(_box(PAD, y, COL_W, pattern, "tgx-flow-call",
                          f"x{count}" if count > 1 else ""))
        parts.append(_arrow(PAD + COL_W, y + BOX_H / 2, mid_x, mid_y + BOX_H / 2))

    right_x = mid_x + MID_W - 40 + 20
    for i, (metric, count) in enumerate(metrics):
        y = GAP + i * (BOX_H + GAP)
        parts.append(_box(right_x, y, RIGHT_W, metric, "tgx-flow-metric",
                          f"{count:,} records"))
        parts.append(_arrow(mid_x + MID_W - 40, mid_y + BOX_H / 2, right_x, y + BOX_H / 2))

    if not endpoints:
        parts.append(f'<text x="{PAD}" y="{height / 2 + 4}" class="tgx-flow-sub">'
                     'no calls in the last run</text>')
    parts.append("</svg>")
    return "".join(parts)
