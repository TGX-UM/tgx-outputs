from . import (  # noqa: F401  (import for side-effect: registration)
    bioconductor,
    citations,
    dockerhub,
    ecosystems,
    ghcr,
    github_graphql,
    rsd,
    services,
    wikipathways,
)
from .base import COLLECTORS, Collector, register, run_all  # noqa: F401
