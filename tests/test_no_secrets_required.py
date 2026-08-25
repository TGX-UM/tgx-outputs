"""The no-secrets invariant.

The moment a collector needs a stored credential, forks stop being able to run CI and
"this runs on nothing but public data" stops being checkable. Keeping it as a test means
adding a secret is a deliberate, visible decision rather than a quiet one.
"""

import os

import pytest

from tgx_outputs import config as _cfg
from tgx_outputs.collect import COLLECTORS
from tgx_outputs.collect.base import run_one
from tgx_outputs.http import HttpClient

SECRETS = ["GITHUB_TOKEN", "GH_TOKEN", "OPENALEX_API_KEY", "ZENODO_TOKEN"]
# Disabled collectors have no fixtures by design: `tgx collect --record` skips them.
# pure_cerif is excluded separately -- its harvest is hundreds of pages, and fixtures
# for it would dwarf the rest of the suite.
OFFLINE = sorted(n for n in COLLECTORS
                 if n != "pure_cerif" and _cfg.collector_enabled(n))


@pytest.fixture
def no_secrets(monkeypatch):
    for name in SECRETS:
        monkeypatch.delenv(name, raising=False)
    assert not any(os.environ.get(n) for n in SECRETS)


@pytest.mark.parametrize("name", OFFLINE)
def test_every_collector_runs_without_any_credential(name, no_secrets):
    with HttpClient(mode="replay") as http:
        env = run_one(COLLECTORS[name], http)
    assert env.status in {"ok", "degraded"}, f"{name} needs a secret: {env.errors[:2]}"
    assert env.records, f"{name} produced nothing without credentials"
