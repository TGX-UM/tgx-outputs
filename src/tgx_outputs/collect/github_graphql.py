"""Releases and activity, per project.

Releases **and** tags are counted, deduplicated per repository and tag. Counting only
GitHub Releases would miss the flagships: BridgeDb ships as the tag `release_3.0.31`
with no Release attached, and BridgeDbR ships through Bioconductor.

Only the repositories listed in config/identifiers.csv are asked about, never a sweep
of thirteen organisations: the dashboard shows the things somebody chose to track.

**Asked in batches.** GraphQL takes aliased fields, so ten repositories fit in one
query. It used to send one query per repository, which is the shape that started
returning 429 from OpenAlex on the citations collector; GitHub had not complained yet,
but a request per tracked thing is a design that gets worse every time the list grows.
A repository that is missing or private comes back as a null field beside the others
rather than failing the request, so one bad name costs one repository instead of ten.
"""

from __future__ import annotations

import datetime as dt
import os

from ..config import excluded_repos, project_field
from ..model import Call, Record
from .base import Collector, register

API = "https://api.github.com/graphql"

# The fields wanted from each repository, written once and referenced by every alias
# in a batch so the query text stays readable however many repositories are in it.
FRAGMENT = """
fragment repoBits on Repository {
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
"""

# Ten repositories at a time: each asks for up to 200 nodes, so a batch of ten is
# nowhere near GitHub's per-query node ceiling while keeping any one request small
# enough to fail cheaply.
BATCH = 10


def _tag_date(node: dict) -> str | None:
    target = node.get("target") or {}
    if target.get("committedDate"):
        return target["committedDate"]
    return ((target.get("target") or {}).get("committedDate"))


@register
class GitHub(Collector):
    name = "github"
    version = "3"

    @staticmethod
    def _absorb(node, project, cutoff, active, per_project, latest) -> None:
        """Fold one repository's answer into the per-project running totals.

        A tag and a Release can describe the same version, so they are merged on the
        tag name before anything is counted -- otherwise every properly published
        release counts twice.
        """
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

        wanted = [(project, repo) for project, repo in project_field("repos")
                  if repo not in excluded and "/" in repo]

        for start in range(0, len(wanted), BATCH):
            chunk = wanted[start:start + BATCH]
            # `r0`, `r1`, ... map each aliased field back to the repository that asked
            # for it; GraphQL will not accept a field name with a slash or a dot in it.
            aliases = {f"r{i}": pair for i, pair in enumerate(chunk)}
            fields = "\n".join(
                f'  {alias}: repository(owner:"{repo.split("/", 1)[0]}", '
                f'name:"{repo.split("/", 1)[1]}") {{ ...repoBits }}'
                for alias, (_project, repo) in aliases.items())
            query = "query {\n" + fields + "\n}\n" + FRAGMENT
            names = ", ".join(repo for _project, repo in chunk)
            try:
                body = self.http.post_json(API, {"query": query}, headers=headers)
            except Exception as exc:  # noqa: BLE001 - one batch must not sink the run
                env.calls.append(Call(url=f"{API} ({len(chunk)} repositories)",
                                      status=None, ok=False, note=str(exc)[:80]))
                env.degrade(f"batch of {len(chunk)} repo(s) failed: {exc}")
                continue
            data = body.get("data") or {}
            returned = sum(1 for alias in aliases if data.get(alias))
            env.calls.append(Call(
                url=f"{API} ({len(chunk)} repositories)", status=200, ok=True,
                note=f"{returned} of {len(chunk)} returned: {names}"[:300]))

            for alias, (project, repo) in aliases.items():
                node = data.get(alias)
                if not node:
                    # Null beside its siblings: the name is wrong, or the repository
                    # is private. Either way it is a config problem worth reporting.
                    env.degrade(f"{repo}: not visible")
                    continue
                self._absorb(node, project, cutoff, active, per_project, latest)

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
