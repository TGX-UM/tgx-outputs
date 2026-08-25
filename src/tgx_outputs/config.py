"""Loading and validating the editable surface."""

from __future__ import annotations

import functools
import hashlib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"


def _load(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing config file: {path}")
    return yaml.safe_load(path.read_text()) or {}


@functools.lru_cache(maxsize=1)
def sources() -> dict[str, Any]:
    return _load("sources.yml")


@functools.lru_cache(maxsize=1)
def semantics() -> dict[str, Any]:
    return _load("metric_semantics.yml")["metrics"]


@functools.lru_cache(maxsize=1)
def exclusions() -> dict[str, Any]:
    return _load("exclusions.yml")


@functools.lru_cache(maxsize=1)
def roster() -> list[str]:
    """The ORCID query set, minus anyone who asked to be excluded."""
    declared = _load("roster.yml").get("orcids") or []
    dropped = {e["value"] for e in (exclusions().get("orcids") or [])}
    return [o for o in declared if o not in dropped]


def collector_enabled(name: str) -> bool:
    return bool(sources().get("collectors", {}).get(name, {}).get("enabled", False))


def cadence_days(name: str) -> int:
    return int(sources().get("collectors", {}).get(name, {}).get("cadence_days", 7))


def config_sha() -> str:
    """Fingerprint of every config file, stamped into each snapshot."""
    h = hashlib.sha256()
    for path in sorted(CONFIG_DIR.glob("*.yml")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


def excluded_repos() -> set[str]:
    return {e["value"] for e in (exclusions().get("repos") or [])}


def excluded_dois() -> set[str]:
    return {e["value"].lower() for e in (exclusions().get("dois") or [])}
