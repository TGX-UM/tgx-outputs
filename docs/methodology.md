# How the numbers are made

Everything comes from public APIs, collected weekly by a job in
[this repository](https://github.com/TGX-UM/tgx-outputs). No manual data entry, no
database, and no credential beyond the token GitHub issues to its own workflow.

## Who counts as TGX

The ORCID list is resolved from the department
[staff page](https://www.maastrichtuniversity.nl/research/translational-genomics/staff).
A surname is matched against ORCID with a Maastricht affiliation and accepted only when
the first initial agrees; anything ambiguous is left out, because a wrong ORCID quietly
credits someone else's papers to the department.

Only ORCIDs are stored. Names and roles are read during resolution and discarded.

## Rules the pipeline enforces

Each exists because a dashboard like this has failed that way before. A record that
trips one is quarantined into the run manifest with its reason and never published.

| Rule | Prevents |
|---|---|
| `semantics_gate` | a figure appearing without a definition of what it counts |
| `period_class` | a running total being filed under a month, which produces identical rows and a headline that sums the same number repeatedly |
| `future_period` | upstream placeholder rows entering the series. Bioconductor ships a zero row for every remaining month of the year |
| `no_silent_zero` | a value collapsing to zero and being published as fact |
| `monotonic` | a lifetime counter appearing to go backwards |
| `empty_result` | a source returning HTTP 200 with no rows being read as "nothing to report" while the last good value ages |
| `rate_limited` | a 429 being absorbed into "handled", which freezes a series while the page claims it is current |
| `volume_drop` | a collapse in record count being promoted |

Freshness comes from each source's own collection timestamp, never from the build
clock. Amber past twice a source's cadence, red past five times.

## Indicator catalogue

--8<-- "methodology.md"

## Sources

| Source | Used for | Terms |
|---|---|---|
| [OpenAlex](https://openalex.org) | publications, open access, citations, co-authorship | CC0 |
| [Crossref](https://www.crossref.org) | coverage comparison | CC0 |
| [Europe PMC](https://europepmc.org) | coverage comparison | EBI terms of use |
| [PubMed](https://www.ncbi.nlm.nih.gov/books/NBK25501/) | coverage comparison | NCBI usage policy |
| [Zenodo](https://zenodo.org) | depositions | metadata CC0 |
| [Bioconductor](https://bioconductor.org/packages/stats/) | downloads, distinct IPs, rank | courtesy files, no stated licence |
| [ecosyste.ms](https://ecosyste.ms) | package discovery and downloads | CC-BY-SA 4.0 |
| [GitHub](https://docs.github.com/en/graphql) | repositories, releases, tags | GitHub API terms |
| [Research Software Directory](https://research-software-directory.org) | literature mentions | Apache-2.0 platform, CC-BY content |
| [ORCID](https://pub.orcid.org) | roster resolution | CC0 |

Only derived aggregates are republished, never a copy of a third-party dataset.

## Charts

Vega-Lite, vendored and pinned rather than loaded from a CDN, so the page renders the
same in five years and archives intact.

| File | Version | SHA-384 |
|---|---|---|
| `vega.min.js` | 5.30.0 | `em7CHpJd+SsMugVFf6TY7AKQcLWMcbPhD84hmNK8o6WFDkK+2uHSUQRVQV1/w827` |
| `vega-lite.min.js` | 5.21.0 | `GhkD6ks9/zgY1m5EFOUZWz/vMVMUFF/92DL61RZc+B42J8osL+jNufKv68bNHHZ2` |
| `vega-embed.min.js` | 6.26.0 | `TqXb8su49m5OnEpKGO8m+VrgHesrUxyP22HgpXi4hnh1Hm43dXroiSYemNf5D8lv` |
