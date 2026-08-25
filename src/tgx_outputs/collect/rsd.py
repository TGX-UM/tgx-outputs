"""Literature mentions, from the Research Software Directory.

The RSD is run by the Netherlands eScience Center and already holds the department's
software: the Maastricht tenant carries BridgeDb, ArrayAnalysis, rWikiPathways,
PathVisio, BridgeDbR, libGPML, PinPath, ToxTempAssistant and more. It harvests GitHub
and Zenodo and computes *mentions* -- scholarly works that name the software -- which
is the impact number that is hardest to compute yourself and the one people actually
want.

Consuming it rather than reimplementing it means a funded team maintains the hard part.
The corollary is that any TGX tool missing from the RSD is invisible here, which is a
reason to register it there rather than a reason to build a second harvester.
"""

from __future__ import annotations

from ..config import sources
from ..model import Call, Record
from .base import Collector, register


@register
class RSD(Collector):
    name = "rsd"
    version = "1"

    def collect(self):
        env = self.envelope()
        cfg = sources().get("rsd") or {}
        base, org = cfg.get("base"), cfg.get("organisation_id")
        if not (base and org):
            env.degrade("no RSD organisation configured")
            return env

        url = f"{base}/rpc/software_by_organisation"
        data = self.http.get_json(url, params={
            "organisation_id": org,
            "select": "brand_name,slug,mention_cnt,contributor_cnt",
            "limit": 200,
        })
        env.calls.append(Call(url=f"{url}?organisation_id={org}", status=200, ok=True,
                              note=f"{len(data)} software entries"))

        for item in data:
            mentions = item.get("mention_cnt")
            if mentions:
                env.records.append(Record(
                    "rsd_mentions", item["brand_name"], float(mentions),
                    extra={"slug": item.get("slug"),
                           "contributors": item.get("contributor_cnt")}))
        if not env.records:
            env.degrade("RSD returned entries but none carried a mention count")
        return env
