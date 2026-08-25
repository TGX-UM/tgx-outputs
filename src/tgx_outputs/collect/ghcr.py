"""Container images published to the GitHub Container Registry.

GHCR reports no pull count, and there is no API that will give one. What it does expose,
anonymously and without any token, is the registry v2 API: the tag list for a public
image, and the creation date of a given tag's manifest.

So this counts what was published and when it last moved, not how much it is used. That
is a real difference and the page says so rather than letting a tag count read as
popularity. Images published to Docker Hub, which does report pulls, are collected
separately.

Private images are skipped silently by design: the anonymous token request simply fails
for them, and listing which images exist but cannot be read would leak the shape of
private infrastructure onto a public page.
"""

from __future__ import annotations

import json

from ..config import project_field
from ..model import Call, Record
from .base import Collector, register

TOKEN = "https://ghcr.io/token"
TAGS = "https://ghcr.io/v2/{image}/tags/list"
MANIFEST = "https://ghcr.io/v2/{image}/manifests/{ref}"
ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


@register
class GHCR(Collector):
    name = "ghcr"
    version = "1"

    def _token(self, image: str) -> str | None:
        try:
            data = self.http.get_json(TOKEN, params={"scope": f"repository:{image}:pull"})
        except Exception:  # noqa: BLE001 - a private image simply has no anonymous token
            return None
        return data.get("token")

    def _published(self, image: str, tag: str, token: str) -> str | None:
        """Creation date of a tag, from the image config blob."""
        try:
            manifest = self.http.get_json(
                MANIFEST.format(image=image, ref=tag),
                headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT},
            )
            digest = (manifest.get("config") or {}).get("digest")
            if not digest:  # multi-arch index: follow the first manifest
                subs = manifest.get("manifests") or []
                if not subs:
                    return None
                inner = self.http.get_json(
                    MANIFEST.format(image=image, ref=subs[0]["digest"]),
                    headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT},
                )
                digest = (inner.get("config") or {}).get("digest")
            if not digest:
                return None
            blob = self.http.get(
                f"https://ghcr.io/v2/{image}/blobs/{digest}",
                headers={"Authorization": f"Bearer {token}"},
            )
            return (json.loads(blob.text).get("created") or "")[:10] or None
        except Exception:  # noqa: BLE001 - dating a tag is a nicety, the count is not
            return None

    def collect(self):
        env = self.envelope()
        images = project_field("ghcr")
        if not images:
            env.degrade("no GHCR images configured")
            return env

        private = 0
        for project, image in images:
            token = self._token(image)
            if not token:
                private += 1
                continue
            try:
                data = self.http.get_json(
                    TAGS.format(image=image),
                    headers={"Authorization": f"Bearer {token}"})
            except Exception:  # noqa: BLE001
                private += 1
                continue
            tags = data.get("tags") or []
            if not tags:
                private += 1
                continue

            env.calls.append(Call(url=TAGS.format(image=image), status=200, ok=True,
                                  note=f"{len(tags)} tags"))
            published = self._published(image, "latest" if "latest" in tags else tags[-1],
                                        token)
            extra = {"project": project}
            if published:
                extra["last_published"] = published
            env.records.append(Record(
                "ghcr_tags", f"ghcr.io/{image}", float(len(tags)), extra=extra))

        if private:
            env.errors.append(f"{private} configured image(s) are private or absent; skipped")
        if not env.records:
            env.degrade("no public GHCR image returned a tag list")
        return env
