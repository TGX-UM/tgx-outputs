"""Bioconductor download statistics.

The whole department's Bioconductor history arrives in a single request. The
``bioc_pkg_stats.tab`` file is roughly 10 MB and 400,000 rows covering every package
back to 2009, with both a download count and a distinct-IP count per month. That file
is parsed in memory and never committed: it is upstream's data, not ours.

Distinct IPs are the series worth reading. Raw download counts include CI runs,
mirrors and container builds; they are collected and shown, but always alongside the
IP series rather than on their own.
"""

from __future__ import annotations

import csv
import datetime as dt
import io

from ..config import sources
from ..model import Call, Record
from .base import Collector, register

STATS_URL = "https://bioconductor.org/packages/stats/bioc/bioc_pkg_stats.tab"
SCORES_URL = "https://bioconductor.org/packages/stats/bioc/bioc_pkg_scores.tab"
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


@register
class Bioconductor(Collector):
    name = "bioconductor"
    version = "1"

    def _wanted(self) -> set[str]:
        return {
            p["name"] for p in sources().get("packages_seed", [])
            if p.get("registry") == "bioconductor.org"
        }

    def collect(self):
        env = self.envelope()
        wanted = self._wanted()
        if not wanted:
            env.degrade("no Bioconductor packages configured")
            return env

        this_month = dt.datetime.now(dt.UTC).strftime("%Y-%m")

        resp = self.http.get(STATS_URL)
        env.calls.append(Call(url=STATS_URL, status=resp.status_code, ok=True,
                              note="all packages, all months, one file"))
        reader = csv.DictReader(io.StringIO(resp.text), delimiter="\t")
        seen = set()
        for row in reader:
            pkg = row.get("Package")
            if pkg not in wanted:
                continue
            month = row.get("Month")
            if month == "all":            # upstream's own yearly roll-up row
                continue
            if month not in MONTHS:
                continue
            period = f"{row['Year']}-{MONTHS[month]:02d}"
            # Upstream ships a zero-valued row for every remaining month of the current
            # calendar year. Those are placeholders, not measurements.
            if period > this_month:
                continue
            seen.add(pkg)
            partial = period == this_month
            env.records.append(Record(
                "bioc_downloads_monthly", pkg, float(row["Nb_of_downloads"]),
                period=period, partial=partial))
            env.records.append(Record(
                "bioc_distinct_ips_monthly", pkg, float(row["Nb_of_distinct_IPs"]),
                period=period, partial=partial))

        missing = wanted - seen
        if missing:
            env.degrade(f"no Bioconductor rows for: {', '.join(sorted(missing))}")

        # Rank comes with a denominator, which is the only reason it is worth showing:
        # "620 of 3,101 packages" can be read, a bare download total cannot.
        try:
            sresp = self.http.get(SCORES_URL)
            env.calls.append(Call(url=SCORES_URL, status=sresp.status_code, ok=True,
                                  note="download score table"))
            rows = list(csv.DictReader(io.StringIO(sresp.text), delimiter="\t"))
            scored = sorted(
                ((r["Package"], float(r["Download_score"])) for r in rows if r.get("Download_score")),
                key=lambda x: -x[1],
            )
            total = len(scored)
            for position, (pkg, _score) in enumerate(scored, start=1):
                if pkg in wanted:
                    env.records.append(Record(
                        "bioc_rank", pkg, position, extra={"of": total}))
        except Exception as exc:  # noqa: BLE001 - rank is optional, downloads are not
            env.degrade(f"rank table unavailable: {exc}")

        return env
