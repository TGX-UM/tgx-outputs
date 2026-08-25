"""Literature mentions, from the Research Software Directory.

The RSD is run by the Netherlands eScience Center. It harvests GitHub and Zenodo and
computes *mentions* -- scholarly works naming a piece of software -- which is the
impact number that is hardest to compute yourself.

Its Maastricht tenant is **university-wide**, so the org listing is filtered against an
explicit allowlist in config. Without that filter the page would report other groups'
software as the department's: the tenant also holds Vantage6, Case Law App, caselawnet,
CrowdED and Verticox+.

A TGX tool missing from the RSD is invisible here. That is a reason to register it
there, not to build a second harvester.
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

        allow = set(cfg.get("allow") or [])
        if not allow:
            env.degrade("no RSD allowlist configured; refusing to report the whole tenant")
            return env

        seen = set()
        for item in data:
            slug = item.get("slug")
            if slug not in allow:
                continue
            seen.add(slug)
            mentions = item.get("mention_cnt")
            if mentions:
                env.records.append(Record(
                    "rsd_mentions", item["brand_name"], float(mentions),
                    extra={"slug": item.get("slug"),
                           "contributors": item.get("contributor_cnt")}))
        missing = allow - seen
        if missing:
            # An allowlisted tool that the tenant no longer lists is worth knowing about:
            # either it was renamed, or it was removed from the organisation.
            env.degrade(f"allowlisted but not in the RSD listing: {', '.join(sorted(missing))}")
        if not env.records:
            env.degrade("no allowlisted tool carried a mention count")
        return env
