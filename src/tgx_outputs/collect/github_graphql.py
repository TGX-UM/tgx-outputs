"""What we shipped, from GitHub.

Releases **and** tags are counted, deduplicated per repository and tag. Counting only
GitHub Releases would under-report precisely the flagship projects: BridgeDb ships as
the tag ``release_3.0.31`` and has no GitHub Release for it, and BridgeDbR ships
through Bioconductor rather than through GitHub at all.

One paginated GraphQL query per organisation pulls repository metadata, the release
list and the tag list together. REST would need one call per repository per fact --
several thousand for the ~430 repositories in scope -- against a 5,000/hour budget.

Repositories are grouped into attribution bands from config and never summed across
them without a qualifier: a repository in the ``wikipathways`` org is co-maintained
with other institutions, not department output.
"""

from __future__ import annotations

import datetime as dt
import os

from ..config import excluded_repos, sources
from ..model import Call, Record
from .base import Collector, register

API = "https://api.github.com/graphql"

QUERY = """
query($login:String!, $cursor:String) {
  repositoryOwner(login:$login) {
    ... on Organization {
      repositories(first:50, after:$cursor, privacy:PUBLIC, isFork:false,
                   orderBy:{field:PUSHED_AT, direction:DESC}) {
        pageInfo { hasNextPage endCursor }
        totalCount
        nodes {
          name pushedAt isArchived
          primaryLanguage { name }
          licenseInfo { spdxId }
          releases(first:100, orderBy:{field:CREATED_AT, direction:DESC}) {
            nodes { tagName publishedAt isPrerelease isDraft }
          }
          refs(refPrefix:"refs/tags/", first:100,
               orderBy:{field:TAG_COMMIT_DATE, direction:DESC}) {
            nodes { name target { ... on Commit { committedDate }
                                  ... on Tag { target { ... on Commit { committedDate } } } } }
          }
        }
      }
    }
  }
}
"""


def _tag_date(node: dict) -> str | None:
    target = node.get("target") or {}
    if target.get("committedDate"):
        return target["committedDate"]
    inner = (target.get("target") or {}).get("committedDate")
    return inner


@register
class GitHub(Collector):
    name = "github"
    version = "1"

    def _token(self) -> str | None:
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def collect(self):
        env = self.envelope()
        token = self._token()
        if not token and self.http.mode == "live":
            # The Actions GITHUB_TOKEN covers this; locally, `gh auth token` does.
            env.degrade("no GITHUB_TOKEN in the environment; GitHub sweep skipped")
            return env

        # In replay mode the fixtures answer the request, so no credential is needed --
        # which is what lets the whole suite run offline and in a fork's CI.
        headers = {"Authorization": f"bearer {token}"} if token else {}
        cutoff = (dt.datetime.now(dt.UTC).date()
                  - dt.timedelta(days=365)).isoformat()
        excluded = excluded_repos()
        per_band_active: dict[str, int] = {}
        releases_by_year: dict[str, set[tuple[str, str]]] = {}

        for org in sources().get("github_orgs", []):
            login, band = org["login"], org.get("band", "community")
            cursor = None
            pages = 0
            while pages < 12:
                payload = {"query": QUERY, "variables": {"login": login, "cursor": cursor}}
                try:
                    body = self.http.post_json(API, payload, headers=headers)
                except Exception as exc:  # noqa: BLE001 - one org must not kill the sweep
                    env.degrade(f"{login}: {exc}")
                    break
                if body.get("errors"):
                    env.degrade(f"{login}: {body['errors'][0].get('message')}")
                    break
                owner = (body.get("data") or {}).get("repositoryOwner")
                if not owner:
                    env.degrade(f"{login}: organisation not visible")
                    break
                pages += 1
                repos = owner["repositories"]
                for node in repos["nodes"]:
                    full = f"{login}/{node['name']}"
                    if full in excluded:
                        continue
                    if not node["isArchived"] and node["pushedAt"][:10] >= cutoff:
                        per_band_active[band] = per_band_active.get(band, 0) + 1

                    stamps: dict[str, str] = {}
                    for rel in node["releases"]["nodes"]:
                        if rel["isDraft"] or not rel.get("publishedAt"):
                            continue
                        stamps[rel["tagName"]] = rel["publishedAt"]
                    for ref in node["refs"]["nodes"]:
                        when = _tag_date(ref)
                        if when and ref["name"] not in stamps:
                            stamps[ref["name"]] = when
                    for tag, when in stamps.items():
                        releases_by_year.setdefault(when[:4], set()).add((full, tag))

                env.calls.append(Call(
                    url=f"{API} ({login} page {pages})", status=200, ok=True,
                    note=f"{repos['totalCount']} public non-fork repos"))
                if not repos["pageInfo"]["hasNextPage"]:
                    break
                cursor = repos["pageInfo"]["endCursor"]

        for band, count in sorted(per_band_active.items()):
            env.records.append(Record("repos_active", band, count))
        for year, pairs in sorted(releases_by_year.items()):
            if year < "2005":
                continue
            env.records.append(Record("releases_by_year", "all", len(pairs), period=year))

        if not env.records:
            env.degrade("GitHub sweep produced no records")
        return env
