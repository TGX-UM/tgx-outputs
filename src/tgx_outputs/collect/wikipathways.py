"""Knowledge infrastructure: WikiPathways.

These numbers are NOT department output and the page must never present them as such.
Pathway content is curated by an international community. What TGX contributes is the
infrastructure around it: the RDF layer, the SPARQL endpoint, GPML tooling and the R
and Python clients. The framing lives in ``metrics.csv`` so it cannot drift
from the figure.

The community endpoint is used rather than the department's own AOP-Wiki multi-release
Virtuoso. That one gives a far better story -- a per-release growth curve going back
years -- but it runs on a two-node swarm with manual DNS failover, so a cluster hiccup
would take the department's public output page stale with it. It is a v2 addition, not
a launch dependency.
"""

from __future__ import annotations

from ..config import sources
from ..model import Call, Record
from .base import Collector, register

PATHWAY_COUNT = """
PREFIX wp: <http://vocabularies.wikipathways.org/wp#>
SELECT (COUNT(DISTINCT ?pathway) AS ?n)
WHERE { ?pathway a wp:Pathway }
"""

SPECIES_COUNT = """
PREFIX wp: <http://vocabularies.wikipathways.org/wp#>
SELECT (COUNT(DISTINCT ?organism) AS ?n)
WHERE { ?pathway a wp:Pathway ; wp:organismName ?organism }
"""


@register
class WikiPathways(Collector):
    name = "wikipathways"
    version = "1"

    def collect(self):
        env = self.envelope()
        entry = next(
            (i for i in sources().get("infrastructure", [])
             if i.get("id") == "wikipathways"), None)
        if not entry or not entry.get("sparql"):
            env.degrade("no WikiPathways SPARQL endpoint configured")
            return env
        endpoint = entry["sparql"]

        for metric, query, label in (
            ("wp_pathway_count", PATHWAY_COUNT, "pathways"),
            ("wp_species_count", SPECIES_COUNT, "species"),
        ):
            rows = self.http.sparql(endpoint, query)
            env.calls.append(Call(url=endpoint, status=200, ok=True,
                                  note=f"{label} count"))
            # An empty result set here is a failure, not a zero: a renamed vocabulary
            # or an endpoint mid-reload returns HTTP 200 with no rows.
            if not rows or not rows[0].get("n"):
                env.degrade(f"{metric}: endpoint returned no rows")
                continue
            env.records.append(Record(metric, "WikiPathways", float(rows[0]["n"])))

        return env
