from . import (  # noqa: F401  (import for side-effect: registration)
    bioconductor,
    coverage,
    dockerhub,
    ecosystems,
    ghcr,
    github_graphql,
    openalex,
    pure_cerif,
    rsd,
    wikipathways,
    zenodo,
)
from .base import COLLECTORS, Collector, register, run_all  # noqa: F401
