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
def projects() -> list[dict[str, Any]]:
    """The tracked projects, in the order they appear in config/projects.yml."""
    return _load("projects.yml").get("projects") or []


def project_ids() -> list[str]:
    return [p["id"] for p in projects()]


def project_field(field: str) -> list[tuple[str, str]]:
    """Flatten one field across projects as (project_id, value) pairs.

    Collectors iterate this rather than a per-source list, which is what keeps
    config/projects.yml the single place a person edits.
    """
    out: list[tuple[str, str]] = []
    for proj in projects():
        for value in proj.get(field) or []:
            out.append((proj["id"], value))
    return out


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


def excluded_packages() -> set[str]:
    return {e["value"] for e in (exclusions().get("packages") or [])}
