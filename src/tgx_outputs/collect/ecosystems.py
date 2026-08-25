"""Package downloads, per project.

One call per package listed in config/projects.yml. Registries report lifetime totals
over different windows and count different things, so downloads are recorded per
package and never added into a single cross-registry number.
"""

from __future__ import annotations

from ..config import excluded_packages, project_field
from ..model import Call, Record
from .base import Collector, register

REGISTRY = "https://packages.ecosyste.ms/api/v1/registries/{reg}/packages/{name}"


@register
class Ecosystems(Collector):
    name = "ecosystems"
    version = "2"

    def collect(self):
        env = self.envelope()
        dropped = excluded_packages()
        seen = 0

        for project, ref in project_field("packages"):
            if ref in dropped or "/" not in ref:
                continue
            reg, name = ref.split("/", 1)
            url = REGISTRY.format(reg=reg, name=name)
            try:
                pkg = self.http.get_json(url)
            except Exception as exc:  # noqa: BLE001 - one package must not sink the run
                env.degrade(f"{ref}: {exc}")
                continue
            seen += 1
            env.calls.append(Call(url=url, status=200, ok=True, note=project))

            env.records.append(Record(
                "registry_breadth", project, 1,
                extra={"registry": reg, "package": name}))

            downloads = pkg.get("downloads")
            if downloads:
                env.records.append(Record(
                    "package_downloads_total", ref, float(downloads),
                    extra={"project": project, "registry": reg,
                           "period_label": pkg.get("downloads_period") or "unknown",
                           "latest_version": pkg.get("latest_release_number")}))

        if not seen:
            env.degrade("no configured package resolved")
        return env
