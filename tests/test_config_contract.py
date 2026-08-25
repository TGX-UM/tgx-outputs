"""Config invariants that a reviewer cannot be expected to hold in their head."""

from tgx_outputs import config as cfg
from tgx_outputs.collect import COLLECTORS
from tgx_outputs.site.charts import CHARTS

REQUIRED = {"label", "counts", "source", "cumulative", "granularity", "caveat"}


def test_every_metric_is_fully_defined():
    for name, spec in cfg.semantics().items():
        assert REQUIRED <= set(spec), f"{name} is missing {sorted(REQUIRED - set(spec))}"
        assert spec["caveat"].strip(), f"{name} has an empty caveat"


def test_cumulative_metrics_declare_no_granularity():
    """A level cannot belong to a period. Enforced in config, not only at runtime."""
    for name, spec in cfg.semantics().items():
        if spec["cumulative"]:
            assert spec["granularity"] == "none", (
                f"{name} is cumulative but declares granularity {spec['granularity']!r}")


def test_every_chart_renders_a_defined_metric():
    semantics = cfg.semantics()
    for chart, (_builder, metric) in CHARTS.items():
        assert metric in semantics, f"chart {chart!r} renders undefined metric {metric!r}"


def test_every_collector_is_configured_and_vice_versa():
    configured = set(cfg.sources().get("collectors", {}))
    assert configured == set(COLLECTORS), (
        f"configured but missing: {sorted(configured - set(COLLECTORS))}; "
        f"implemented but unconfigured: {sorted(set(COLLECTORS) - configured)}")


def test_exclusions_always_carry_a_reason():
    for kind, entries in cfg.exclusions().items():
        for entry in entries or []:
            assert entry.get("reason"), f"{kind}: {entry} has no reason"


def test_no_config_file_names_a_person():
    """The privacy promise, as a test rather than a paragraph in a README.

    Every target is a repository, package, image, endpoint or DOI. Nothing here is
    queried by person, so an ORCID appearing in config would be a change of scope
    rather than a typo.
    """
    for path in sorted(cfg.CONFIG_DIR.glob("*.yml")):
        text = path.read_text()
        assert "orcid" not in text.lower(), (
            f"{path.name} mentions ORCID; this dashboard queries software, not people")
