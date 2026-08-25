"""Container pulls, from Docker Hub.

Docker Hub is the only registry the department publishes to that reports a pull count.
It is a lifetime counter, stored as such and never filed under a period; "new pulls
this month" comes from differencing consecutive snapshots.

The number is inflated in ways nobody can separate out. A CI job that rebuilds hourly
pulls its base image every time, and one pull of a multi-arch image can register more
than once. Reach, not installs.
"""

from __future__ import annotations

from ..config import excluded_packages, project_field
from ..model import Call, Record
from .base import Collector, register

REPO = "https://hub.docker.com/v2/repositories/{image}/"


@register
class DockerHub(Collector):
    name = "dockerhub"
    version = "2"

    def collect(self):
        env = self.envelope()
        images = project_field("docker")
        if not images:
            env.degrade("no Docker Hub images configured")
            return env

        dropped = excluded_packages()
        for project, image in images:
            if image in dropped:
                continue
            url = REPO.format(image=image)
            try:
                repo = self.http.get_json(url)
            except Exception as exc:  # noqa: BLE001
                env.degrade(f"{image}: {exc}")
                continue
            pulls = repo.get("pull_count")
            env.calls.append(Call(url=url, status=200, ok=True, note=project))
            if pulls:
                env.records.append(Record(
                    "docker_pulls_total", image, float(pulls),
                    extra={"project": project,
                           "last_updated": (repo.get("last_updated") or "")[:10]}))

        if not env.records:
            env.degrade("no configured image returned a pull count")
        return env
