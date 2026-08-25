"""Package downloads, per project.

One call per package listed in config/projects.yml.

Registries do not report the same thing, and the difference is not cosmetic.
Bioconductor and CRAN publish a lifetime counter; npm and PyPI publish no such figure,
so ecosyste.ms returns a rolling 30-day count for them and says which it is in
``downloads_period``. Filing both under one "downloads" metric produced a tile reading
"747, all time" that was in fact last month, and a per-project column that added a
lifetime figure to a 30-day one.

So the window decides the metric. A lifetime counter goes to ``package_downloads_total``
(cumulative, watched by the monotonic guard); a rolling window goes to
``package_downloads_recent`` (not cumulative, because a quiet month is legitimately
lower than a busy one and the monotonic guard would quarantine it as a counter running
backwards). A window this code does not recognise is not published at all -- an
undefined measure is exactly what the semantics gate exists to stop.
"""

from __future__ import annotations

from ..config import excluded_packages, project_field
from ..model import Call, Record
from .base import Collector, register

REGISTRY = "https://packages.ecosyste.ms/api/v1/registries/{reg}/packages/{name}"

# ecosyste.ms self-declares the window in `downloads_period`. Anything not listed here
# is left uncollected rather than guessed at.
WINDOWS = {
    "total": "package_downloads_total",
    "last-month": "package_downloads_recent",
}


@register
class Ecosystems(Collector):
    name = "ecosystems"
    version = "3"

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
                window = pkg.get("downloads_period") or "unknown"
                metric = WINDOWS.get(window)
                if metric is None:
                    env.degrade(
                        f"{ref}: ecosyste.ms reports downloads over {window!r}, which has "
                        "no metric defined; not published")
                    continue
                env.records.append(Record(
                    metric, ref, float(downloads),
                    extra={"project": project, "registry": reg,
                           "period_label": window,
                           "latest_version": pkg.get("latest_release_number")}))

        if not seen:
            env.degrade("no configured package resolved")
        return env
