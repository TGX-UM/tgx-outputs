"""Releases and activity, per project.

Releases **and** tags are counted, deduplicated per repository and tag. Counting only
GitHub Releases would miss the flagships: BridgeDb ships as the tag `release_3.0.31`
with no Release attached, and BridgeDbR ships through Bioconductor.

One GraphQL query per repository listed in config/identifiers.csv. That is a couple of
dozen calls rather than a sweep of thirteen organisations, which is the point: the
dashboard shows the things somebody chose to track.
"""

from __future__ import annotations

import datetime as dt
import os

from ..config import excluded_repos, project_field
from ..model import Call, Record
from .base import Collector, register

API = "https://api.github.com/graphql"

QUERY = """
query($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    nameWithOwner pushedAt isArchived stargazerCount
    primaryLanguage { name }
    licenseInfo { spdxId }
    releases(first:100, orderBy:{field:CREATED_AT, direction:DESC}) {
      nodes { tagName publishedAt isDraft }
    }
    refs(refPrefix:"refs/tags/", first:100,
         orderBy:{field:TAG_COMMIT_DATE, direction:DESC}) {
      nodes { name target { ... on Commit { committedDate }
                            ... on Tag { target { ... on Commit { committedDate } } } } }
    }
  }
}
"""


def _tag_date(node: dict) -> str | None:
    target = node.get("target") or {}
    if target.get("committedDate"):
        return target["committedDate"]
    return ((target.get("target") or {}).get("committedDate"))


@register
class GitHub(Collector):
    name = "github"
    version = "2"

    def collect(self):
        env = self.envelope()
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token and self.http.mode == "live":
            env.degrade("no GITHUB_TOKEN in the environment; GitHub skipped")
            return env
        headers = {"Authorization": f"bearer {token}"} if token else {}

        excluded = excluded_repos()
        cutoff = (dt.datetime.now(dt.UTC).date() - dt.timedelta(days=365)).isoformat()
        per_project: dict[str, set[tuple[str, str]]] = {}
        active: dict[str, int] = {}
        latest: dict[str, str] = {}

        for project, repo in project_field("repos"):
            if repo in excluded or "/" not in repo:
                continue
            owner, name = repo.split("/", 1)
            try:
                body = self.http.post_json(
                    API, {"query": QUERY, "variables": {"owner": owner, "name": name}},
                    headers=headers)
            except Exception as exc:  # noqa: BLE001 - one repo must not sink the run
                env.degrade(f"{repo}: {exc}")
                continue
            node = (body.get("data") or {}).get("repository")
            if not node:
                env.degrade(f"{repo}: not visible")
                continue

            env.calls.append(Call(url=f"{API} ({repo})", status=200, ok=True,
                                  note=f"pushed {node['pushedAt'][:10]}"))
            if not node["isArchived"] and node["pushedAt"][:10] >= cutoff:
                active[project] = active.get(project, 0) + 1

            stamps: dict[str, str] = {}
            for rel in node["releases"]["nodes"]:
                if not rel["isDraft"] and rel.get("publishedAt"):
                    stamps[rel["tagName"]] = rel["publishedAt"]
            for ref in node["refs"]["nodes"]:
                when = _tag_date(ref)
                if when and ref["name"] not in stamps:
                    stamps[ref["name"]] = when
            for tag, when in stamps.items():
                per_project.setdefault(project, set()).add((tag, when[:10]))
                if when[:10] > latest.get(project, ""):
                    latest[project] = when[:10]

        for project, pairs in sorted(per_project.items()):
            by_year: dict[str, int] = {}
            for _tag, when in pairs:
                by_year[when[:4]] = by_year.get(when[:4], 0) + 1
            for year, count in sorted(by_year.items()):
                if year >= "2005":
                    env.records.append(
                        Record("releases_by_year", project, count, period=year))
            env.records.append(Record(
                "latest_release", project, 1,
                extra={"date": latest.get(project, "")}))

        for project, count in sorted(active.items()):
            env.records.append(Record("repos_active", project, count))

        if not env.records:
            env.degrade("GitHub produced no records")
        return env
