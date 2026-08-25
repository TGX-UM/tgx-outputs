"""Citations of the papers that describe each tool.

This is the number people mean by "how much is it used". It is not the same as the
Research Software Directory's mention count, which comes from a text-mining dataset
that is badly incomplete: it reports 6 for rWikiPathways and 237 for BridgeDb, where
the actual citation counts are thousands and hundreds. Both are collected, and the page
labels which is which.

Every update paper is counted, not only the newest. WikiPathways has six NAR papers
spanning 2012 to 2024 and people cite whichever was current when they did the work, so
counting one would understate it several-fold.

One request per DOI, each logged individually, because the published call list is the
whole point of the explainability page: a reader should be able to see every question
this dashboard asked and go and ask it themselves.

Two honesty constraints, both stated in the metric caveats rather than left implicit.
A citation of the software paper is not proof the software was used, and some of these
tools are built by consortia far larger than this department. CDK's citations belong to
its whole community, not to TGX.
"""

from __future__ import annotations

import os
import urllib.parse

from ..config import excluded_dois, project_field
from ..model import Call, Record
from .base import Collector, register

WORK = "https://api.openalex.org/works/doi:{doi}"


@register
class Citations(Collector):
    name = "citations"
    version = "1"

    def collect(self):
        env = self.envelope()
        papers = project_field("papers")
        if not papers:
            env.degrade("no project lists a paper DOI")
            return env

        dropped = excluded_dois()
        key = os.environ.get("OPENALEX_API_KEY")
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        missing: list[str] = []

        for project, doi in papers:
            doi = str(doi).strip()
            if doi.lower() in dropped:
                continue
            params = {"select": "doi,title,publication_year,cited_by_count,type"}
            if key:
                params["api_key"] = key
            url = WORK.format(doi=urllib.parse.quote(doi, safe="/.:"))
            try:
                work = self.http.get_json(url, params=params)
            except Exception as exc:  # noqa: BLE001 - one DOI must not sink the run
                # Logged as the failed call it was, so the published call list stays a
                # complete record of what this collector asked for.
                env.calls.append(Call(url=url, status=None, ok=False, note=str(exc)[:80]))
                missing.append(f"{doi} ({exc})")
                continue
            env.calls.append(Call(url=url, status=200, ok=True, note=project))

            cited = work.get("cited_by_count")
            if cited is None:
                missing.append(doi)
                continue
            totals[project] = totals.get(project, 0.0) + float(cited)
            counts[project] = counts.get(project, 0) + 1
            env.records.append(Record(
                "paper_citations_by_doi", doi, float(cited),
                extra={"project": project,
                       "year": work.get("publication_year"),
                       # A preprint is labelled as one on the page. Several tools are
                       # described by one so far, and a reader should not have to
                       # follow the DOI to find out that is what they are getting.
                       "type": work.get("type"),
                       "title": (work.get("title") or "")[:90]}))

        for project, total in sorted(totals.items()):
            env.records.append(Record(
                "paper_citations", project, total,
                extra={"papers": counts[project]}))

        if missing:
            # A DOI that does not resolve is a config error, and silently returning a
            # smaller number is exactly the failure this dashboard is built to avoid.
            env.degrade(f"{len(missing)} DOI(s) did not resolve: {', '.join(missing[:3])}")
        return env
