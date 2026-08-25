"""Container pulls, from Docker Hub.

Docker Hub is the only registry the department publishes to that reports a pull count
at all. GHCR reports none, which is why images published there are counted by their
tags and releases rather than by use.

The number is a lifetime counter and is stored as such: never filed under a period,
and turned into "new pulls this month" by differencing consecutive snapshots. It is
also inflated in ways nobody can separate out. A CI job that rebuilds hourly pulls the
base image every time, and a single `docker pull` of a multi-arch image can register
more than once. Read it as reach, not as installs.
"""

from __future__ import annotations

from ..config import excluded_packages, sources
from ..model import Call, Record
from .base import Collector, register

NAMESPACE = "https://hub.docker.com/v2/repositories/{ns}/"


@register
class DockerHub(Collector):
    name = "dockerhub"
    version = "1"

    def collect(self):
        env = self.envelope()
        namespaces = sources().get("dockerhub", {}).get("namespaces") or []
        if not namespaces:
            env.degrade("no Docker Hub namespaces configured")
            return env

        excluded = excluded_packages()
        for ns in namespaces:
            url = NAMESPACE.format(ns=ns)
            try:
                data = self.http.get_json(url, params={"page_size": 100})
            except Exception as exc:  # noqa: BLE001 - one namespace must not sink the rest
                env.degrade(f"{ns}: {exc}")
                continue

            results = data.get("results", [])
            env.calls.append(Call(url=url, status=200, ok=True,
                                  note=f"{data.get('count', len(results))} repositories"))
            for repo in results:
                entity = f"{ns}/{repo['name']}"
                if entity in excluded:
                    continue
                pulls = repo.get("pull_count")
                if not pulls:
                    continue
                env.records.append(Record(
                    "docker_pulls_total", entity, float(pulls),
                    extra={"last_updated": (repo.get("last_updated") or "")[:10]}))

        if not env.records:
            env.degrade("no Docker Hub repositories returned a pull count")
        return env
