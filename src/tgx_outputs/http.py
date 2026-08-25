"""The one HTTP client.

Two properties matter more than anything else here:

* **Timeouts are not optional.** They are set on the client, so no collector can
  forget one. An unbounded request is how a cron job hangs until the runner is killed
  and the refresh produces nothing at all.
* **A 429 is never swallowed.** ``RateLimited`` propagates so the collector can mark
  its source degraded. Retry logic that quietly returns partial data is how a series
  freezes while the page keeps claiming it is fresh.

``replay`` mode reads recorded responses from tests/fixtures so the whole test suite
and ``make offline`` run with no network at all.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

USER_AGENT = (
    "tgx-outputs/0.1 (+https://github.com/TGX-UM/tgx-outputs; "
    "mailto:marvin.martens@maastrichtuniversity.nl)"
)
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


class RateLimited(RuntimeError):
    """HTTP 429 or an explicit quota refusal. Always surfaces; never absorbed."""


class HttpError(RuntimeError):
    pass


def _fixture_name(method: str, url: str, params: Any) -> str:
    blob = f"{method} {url} {json.dumps(params, sort_keys=True, default=str)}"
    return hashlib.sha256(blob.encode()).hexdigest()[:16] + ".json"


class HttpClient:
    def __init__(
        self,
        mode: str | None = None,
        fixture_dir: Path | None = None,
        max_calls: int | None = None,
    ) -> None:
        self.mode = mode or os.environ.get("TGX_HTTP_MODE", "live")
        self.fixture_dir = fixture_dir or Path(__file__).resolve().parents[2] / "tests" / "fixtures"
        self.max_calls = max_calls
        self.calls = 0
        self._client: httpx.Client | None = None

    def _ensure(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=TIMEOUT,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ get
    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 2,
    ) -> httpx.Response:
        if self.max_calls is not None and self.calls >= self.max_calls:
            raise HttpError(f"call budget of {self.max_calls} exhausted before {url}")
        self.calls += 1

        path = self.fixture_dir / _fixture_name("GET", url, params or {})
        if self.mode == "replay":
            if not path.exists():
                raise HttpError(f"no fixture for GET {url} params={params} ({path.name})")
            blob = json.loads(path.read_text())
            return httpx.Response(
                status_code=blob["status"],
                text=blob["text"],
                request=httpx.Request("GET", url, params=params),
            )

        client = self._ensure()
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = client.get(url, params=params, headers=headers)
            except httpx.HTTPError as exc:  # network-level
                last = exc
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise HttpError(f"GET {url}: {exc}") from exc

            if resp.status_code == 429:
                # Deliberately not retried into silence. The caller degrades.
                raise RateLimited(f"GET {url}: 429 rate limited")
            if resp.status_code >= 500 and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise HttpError(f"GET {url}: HTTP {resp.status_code}")

            if self.mode == "record":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(
                        {"url": url, "params": params, "status": resp.status_code,
                         "text": resp.text},
                        indent=1,
                    )
                )
            return resp

        raise HttpError(f"GET {url}: exhausted retries ({last})")

    def get_json(self, url: str, params: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self.get(url, params=params, **kw).json()

    # ----------------------------------------------------------------- post
    def post_json(
        self,
        url: str,
        json_body: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Any:
        """POST a JSON body. Used for GraphQL, and recorded/replayed like a GET."""
        if self.max_calls is not None and self.calls >= self.max_calls:
            raise HttpError(f"call budget of {self.max_calls} exhausted before {url}")
        self.calls += 1

        path = self.fixture_dir / _fixture_name("POST", url, json_body)
        if self.mode == "replay":
            if not path.exists():
                raise HttpError(f"no fixture for POST {url} ({path.name})")
            return json.loads(json.loads(path.read_text())["text"])

        resp = self._ensure().post(url, json=json_body, headers=headers)
        if resp.status_code == 429:
            raise RateLimited(f"POST {url}: 429 rate limited")
        if resp.status_code >= 400:
            raise HttpError(f"POST {url}: HTTP {resp.status_code}")
        if self.mode == "record":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(
                {"url": url, "body": json_body, "status": resp.status_code,
                 "text": resp.text}, indent=1))
        return resp.json()

    def sparql(self, endpoint: str, query: str) -> list[dict[str, str]]:
        """Run a SPARQL SELECT and return rows as flat dicts.

        Uses ``Accept: text/csv``, which every endpoint we query answers, so there is
        no SPARQLWrapper dependency and no XML parsing.
        """
        import csv
        import io

        resp = self.get(
            endpoint,
            params={"query": query},
            headers={"Accept": "text/csv"},
        )
        return list(csv.DictReader(io.StringIO(resp.text)))
