"""The running services, not just the code that builds them.

BridgeDb and WikiPathways are web services and web sites as much as they are packages,
and a page that shows only releases and downloads undersells them badly.

What is counted here is what the department actually produces for those services, and
not the community content they carry:

* BridgeDb's mapping databases are built by the department from the primary sources and
  deposited with a DOI. Their downloads are department output by any reading.

The SPARQL endpoints are listed as services the department runs, but nothing about
their contents is measured. A triple count was published here until 2026-08-25 and was
withdrawn: the number is the size of a corpus international communities curate, and no
caption made it read as anything other than a score for this department.

Zenodo statistics are read per record by DOI. That matters: the same numbers taken from
Zenodo's *search listing* are reported against whichever version the search returns and
move between runs, which is why dataset downloads are collected this way and not that
way.

Uptime is deliberately not measured. Whether a service responded during one weekly run
says almost nothing, and treating it as a status page would be misleading.
"""

from __future__ import annotations

from ..config import projects
from ..model import Call, Record
from .base import Collector, register

ZENODO = "https://zenodo.org/api/records/{rid}"


@register
class Services(Collector):
    name = "services"
    version = "2"

    # -- probe types ---------------------------------------------------------
    def _bridgedb_contents(self, env, project: str, url: str) -> None:
        resp = self.http.get(url)
        env.calls.append(Call(url=url, status=resp.status_code, ok=True, note="species list"))
        species = [ln for ln in resp.text.splitlines() if ln.strip()]
        if not species:
            env.degrade(f"{project}: /contents returned nothing")
            return
        env.records.append(Record("species_served", project, float(len(species))))

    def _bridgedb_manifest(self, env, project: str, url: str) -> None:
        data = self.http.get_json(url)
        files = data.get("mappingFiles") or []
        env.calls.append(Call(url=url, status=200, ok=True, note=f"{len(files)} mapping files"))
        if not files:
            env.degrade(f"{project}: manifest listed no mapping files")
            return
        env.records.append(Record("mapping_databases", project, float(len(files))))

        total = 0.0
        seen: set[str] = set()
        for doi in sorted({f.get("doi") for f in files if f.get("doi")}):
            rid = doi.rsplit(".", 1)[-1]
            if not rid.isdigit():
                continue
            try:
                record = self.http.get_json(ZENODO.format(rid=rid))
            except Exception:  # noqa: BLE001 - a concept DOI or a withdrawn record
                continue
            unique = (record.get("stats") or {}).get("unique_downloads")
            if unique:
                seen.add(doi)
                total += float(unique)
        if seen:
            env.records.append(Record(
                "dataset_downloads", project, total, extra={"records": len(seen)}))

    # -- run -----------------------------------------------------------------
    def collect(self):
        env = self.envelope()
        handlers = {
            "bridgedb_contents": self._bridgedb_contents,
            "bridgedb_manifest": self._bridgedb_manifest,
        }

        probes = 0
        for proj in projects():
            for kind, url in (proj.get("probes") or {}).items():
                handler = handlers.get(kind)
                if handler is None:
                    env.degrade(f"{proj['id']}: no handler for probe type {kind!r}")
                    continue
                probes += 1
                try:
                    handler(env, proj["id"], url)
                except Exception as exc:  # noqa: BLE001 - one probe must not sink the run
                    env.degrade(f"{proj['id']}/{kind}: {exc}")

        # Count the services themselves, which is a fact about the page rather than a
        # measurement: it is what the department runs, whether or not it is probeable.
        running = sum(len(p.get("services") or []) for p in projects())
        if running:
            env.records.append(Record("services_run", "all", float(running)))

        if not probes:
            env.degrade("no project declares a probe")
        return env
