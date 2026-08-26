"""Collector contract and the run loop.

A collector is one class with one method. It returns an :class:`Envelope` and never
touches the filesystem, which is what makes every collector testable offline and makes
a single broken source unable to take the run down with it.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable

from ..config import collector_enabled
from ..http import HttpClient, RateLimited
from ..model import Envelope

COLLECTORS: dict[str, type[Collector]] = {}


class Collector:
    name: str = "unnamed"
    version: str = "1"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(self) -> Envelope:  # pragma: no cover - interface
        raise NotImplementedError

    # helper used by every subclass
    def envelope(self) -> Envelope:
        return Envelope(source=self.name, collector_version=self.version)


def register(cls: type[Collector]) -> type[Collector]:
    COLLECTORS[cls.name] = cls
    return cls


def run_one(cls: type[Collector], http: HttpClient) -> Envelope:
    """Run a collector with total failure isolation.

    A rate-limit is degraded rather than retried into silence; anything else that
    escapes becomes a failed source with its traceback in the manifest. Either way the
    run continues and the site still builds.
    """
    inst = cls(http)
    try:
        return inst.collect()
    except RateLimited as exc:
        env = Envelope(source=cls.name, collector_version=cls.version)
        env.degrade(f"rate limited: {exc}")
        return env
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all at the boundary
        env = Envelope(source=cls.name, collector_version=cls.version)
        env.fail(f"{type(exc).__name__}: {exc}")
        env.errors.append(traceback.format_exc(limit=3))
        return env


def run_all(
    http: HttpClient,
    only: list[str] | None = None,
    on_start: Callable[[str], None] | None = None,
) -> dict[str, Envelope]:
    out: dict[str, Envelope] = {}
    for name, cls in COLLECTORS.items():
        if only and name not in only:
            continue
        if not only and not collector_enabled(name):
            out[name] = Envelope(source=name, status="skipped",
                                 errors=["disabled in config/collectors.csv"])
            continue
        if on_start:
            on_start(name)
        out[name] = run_one(cls, http)
    return out
