"""Citations of the papers that describe each tool.

This is the number people mean by "how much is it used". It is not the same as the
Research Software Directory's mention count, which comes from a text-mining dataset
that is badly incomplete: it reports 6 for rWikiPathways and 237 for BridgeDb, where
the actual citation counts are thousands and hundreds. Both are collected, and the page
labels which is which.

Every update paper is counted, not only the newest. WikiPathways has six NAR papers
spanning 2012 to 2024 and people cite whichever was current when they did the work, so
counting one would understate it several-fold.

**Asked in batches, not one DOI at a time.** OpenAlex takes an OR filter, so every DOI
this project tracks fits in a single request. It used to ask once per DOI, which was
fine at a dozen papers and started returning 429 at twenty-five -- the run on
2026-08-26 lost five papers that way. Batching is not a workaround for the rate limit:
one request for twenty-five facts is simply the right request, and it keeps the
published call list shorter and more legible rather than less. The whole filter,
including every DOI in it, is recorded in that list.

Two honesty constraints, both stated in the metric caveats rather than left implicit.
A citation of the software paper is not proof the software was used, and some of these
tools are built by consortia far larger than this department. CDK's citations belong to
its whole community, not to TGX.
"""

from __future__ import annotations

import os

from ..config import excluded_dois, project_field, sources
from ..model import Call, Record
from .base import Collector, register

WORKS = "https://api.openalex.org/works"

# OpenAlex accepts up to 50 values in an OR filter. Twenty-five leaves headroom and
# keeps any one URL short enough to read on the calls page.
BATCH = 25


def _bare(doi: str) -> str:
    """`https://doi.org/10.x/y`, `doi:10.x/y` and `10.x/y` are the same identifier."""
    doi = str(doi).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


@register
class Citations(Collector):
    name = "citations"
    version = "2"

    def collect(self):
        env = self.envelope()
        papers = project_field("papers")
        if not papers:
            env.degrade("no project lists a paper DOI")
            return env

        dropped = excluded_dois()
        # One DOI can describe more than one tracked project, so this is a list.
        owners: dict[str, list[str]] = {}
        order: list[str] = []
        for project, doi in papers:
            bare = _bare(doi)
            if bare in dropped:
                continue
            if bare not in owners:
                order.append(bare)
            owners.setdefault(bare, []).append(project)

        params_base = {"select": "doi,title,publication_year,cited_by_count,type",
                       "per-page": BATCH}
        # OpenAlex's polite pool. Without it a shared runner IP is throttled with
        # everyone else calling from CI; with it the request is attributable and
        # gets the higher limit.
        contact = sources().get("meta", {}).get("contact")
        if contact:
            params_base["mailto"] = contact
        key = os.environ.get("OPENALEX_API_KEY")
        if key:
            params_base["api_key"] = key

        found: dict[str, dict] = {}
        for start in range(0, len(order), BATCH):
            chunk = order[start:start + BATCH]
            params = {**params_base, "filter": "doi:" + "|".join(chunk)}
            try:
                page = self.http.get_json(WORKS, params=params)
            except Exception as exc:  # noqa: BLE001 - one batch must not sink the run
                env.calls.append(Call(url=WORKS, status=None, ok=False,
                                      note=str(exc)[:80]))
                env.degrade(f"batch of {len(chunk)} DOI(s) failed: {exc}")
                continue
            results = page.get("results") or []
            env.calls.append(Call(url=WORKS, status=200, ok=True,
                                  note=f"{len(chunk)} DOIs asked, {len(results)} returned"))
            for work in results:
                found[_bare(work.get("doi") or "")] = work

        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        missing: list[str] = []
        for doi in order:
            work = found.get(doi)
            cited = work.get("cited_by_count") if work else None
            if cited is None:
                missing.append(doi)
                continue
            env.records.append(Record(
                "paper_citations_by_doi", doi, float(cited),
                extra={"project": owners[doi][0],
                       "year": work.get("publication_year"),
                       # A preprint is labelled as one on the page. Several tools are
                       # described by one so far, and a reader should not have to
                       # follow the DOI to find out that is what they are getting.
                       "type": work.get("type"),
                       "title": (work.get("title") or "")[:90]}))
            for project in owners[doi]:
                totals[project] = totals.get(project, 0.0) + float(cited)
                counts[project] = counts.get(project, 0) + 1

        for project, total in sorted(totals.items()):
            env.records.append(Record(
                "paper_citations", project, total,
                extra={"papers": counts[project]}))

        env.expected, env.found, env.unit = len(order), len(order) - len(missing), "papers"
        if missing:
            # OpenAlex returned no work for these. That is not the same as the DOI being
            # broken: it resolves at doi.org perfectly well, OpenAlex simply does not
            # index it, which is ordinary for Figshare and Zenodo deposits. Still worth
            # degrading, because a tracked paper contributing zero to the total is a gap
            # the page should admit to rather than absorb. The fix is either to wait for
            # OpenAlex to pick it up or to record in exclusions.csv why it is not counted.
            env.degrade(
                f"OpenAlex has no record for {len(missing)} DOI(s): "
                f"{', '.join(missing[:3])}")
        return env
