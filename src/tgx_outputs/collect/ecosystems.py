"""Package discovery and cross-registry reach, via ecosyste.ms.

The useful trick here is the reverse lookup: given a repository URL, ecosyste.ms
returns the registry packages built from it. That means the package list is discovered
rather than hand-maintained -- the thing that most reliably goes stale in a dashboard
like this is a list of names somebody has to remember to update.

Only ``packages.ecosyste.ms`` is used. The repos service is not: its owner-level
aggregates are badly stale (the wikipathways owner record was last synced in April
2024), so GitHub stays the source of truth for repository facts. The summary service
is avoided entirely because its lookup endpoint has side effects -- a GET creates a
record -- which has no place in a cron job.
"""

from __future__ import annotations

from ..config import excluded_packages, excluded_repos, sources
from ..model import Call, Record
from .base import Collector, register

LOOKUP = "https://packages.ecosyste.ms/api/v1/packages/lookup"
REGISTRY = "https://packages.ecosyste.ms/api/v1/registries/{reg}/packages/{name}"


@register
class Ecosystems(Collector):
    name = "ecosystems"
    version = "1"

    def collect(self):
        env = self.envelope()
        found: dict[tuple[str, str], dict] = {}

        # 1. discovery: repository -> published packages
        for repo in sources().get("flagship_repos", []):
            if repo in excluded_repos():
                continue
            url = f"https://github.com/{repo}"
            try:
                data = self.http.get_json(LOOKUP, params={"repository_url": url})
            except Exception as exc:  # noqa: BLE001
                env.degrade(f"lookup failed for {repo}: {exc}")
                continue
            env.calls.append(Call(url=f"{LOOKUP}?repository_url={url}", status=200, ok=True,
                                  note=f"{len(data)} package(s)"))
            for pkg in data:
                reg = (pkg.get("registry") or {}).get("name")
                if reg and pkg.get("name"):
                    found[(reg, pkg["name"])] = pkg
                    env.records.append(Record(
                        "registry_breadth", repo, 1,
                        extra={"registry": reg, "package": pkg["name"]}))

        # 2. seeded packages we already know about
        for entry in sources().get("packages_seed", []):
            reg, name = entry["registry"], entry["name"]
            if (reg, name) in found:
                continue
            try:
                found[(reg, name)] = self.http.get_json(
                    REGISTRY.format(reg=reg, name=name))
            except Exception as exc:  # noqa: BLE001
                env.degrade(f"{reg}/{name}: {exc}")

        # 3. the numbers
        dropped = excluded_packages()
        for (reg, name), pkg in sorted(found.items()):
            if f"{reg}/{name}" in dropped:
                continue
            downloads = pkg.get("downloads")
            if downloads:
                # A LEVEL, never a flow: registries report a lifetime counter, and the
                # period they cover differs between them, so these are shown per
                # registry and never summed into one cross-registry total.
                env.records.append(Record(
                    "package_downloads_total", f"{reg}/{name}", float(downloads),
                    extra={"registry": reg, "package": name,
                           "period_label": pkg.get("downloads_period") or "unknown",
                           "latest_version": pkg.get("latest_release_number")}))

        if not found:
            env.degrade("no packages discovered or resolved")
        return env
