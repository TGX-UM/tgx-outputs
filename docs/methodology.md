# How the numbers are made

Everything on this site comes from public APIs, collected once a week by a scheduled
job in [this repository](https://github.com/TGX-UM/tgx-outputs). There is no manual
data entry, no private database, and no credential beyond the token GitHub issues to
its own workflow.

## Who counts as TGX

Maastricht University publishes its research information system as an
[OpenAIRE CERIF feed](https://cris.maastrichtuniversity.nl/ws/oai?verb=Identify) over
OAI-PMH, with no authentication. Person records in that feed carry both an ORCID and an
organisational-unit affiliation, and Translational Genomics has a unit identifier:
`aa0b41cd-a526-424c-8515-f8f789aa92b1`.

The department roster is therefore *derived* from the university's own records rather
than hand-maintained. That matters for two reasons. A hand-maintained list of
colleagues goes stale silently, and a stale roster produces a smaller,
fresher-looking wrong number. And deriving membership from Pure means these figures
reconcile with what the department already reports to its faculty, instead of quietly
becoming a second set of books.

Only ORCIDs are kept. Names, roles and employment dates are read during the harvest and
discarded.

## Rules the pipeline enforces

Each of these exists because a dashboard of this kind has actually failed this way.
Each is a unit test, and a record that trips one is quarantined — recorded in the run
manifest with its reason, never published — because a confidently wrong number does
more damage than a missing one.

| Rule | What it prevents |
|---|---|
| `semantics_gate` | A figure appearing without a published definition of what it counts. Nothing renders unless it is defined on this page. |
| `period_class` | An all-time counter being filed under a month. That produces identical consecutive rows and a headline total that is a sum of duplicated snapshots. |
| `future_period` | Upstream placeholder rows entering the series. Bioconductor's statistics table ships a zero-valued row for every remaining month of the calendar year. |
| `no_silent_zero` | A value collapsing to zero and being published as fact. |
| `monotonic` | A lifetime counter appearing to go backwards. |
| `empty_result` | A source returning HTTP 200 with no rows — a renamed graph, an endpoint mid-reload — being read as "nothing to report" while the last good value silently ages. |
| `rate_limited` | A 429 being absorbed by retry logic into "handled", which freezes a series while the page keeps claiming it is current. |
| `volume_drop` | A collapse in record count being promoted. Nothing is published from that source that run. |

Freshness is computed from each source's own collection timestamp, never from the
time the page was built. A page that renders the build clock in a "last updated" line
is claiming a currency it has not checked.

## Indicator catalogue

Every metric, what one unit of it is, and what it does not mean.

--8<-- "methodology.md"

## Sources and attribution

| Source | Used for | Terms |
|---|---|---|
| [OpenAlex](https://openalex.org) | publications, open access, citations, collaboration | CC0 |
| [Crossref](https://www.crossref.org) | coverage comparison | CC0 |
| [Europe PMC](https://europepmc.org) | coverage comparison | see EBI terms of use |
| [PubMed / NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) | coverage comparison | NCBI usage policy |
| [Zenodo](https://zenodo.org) | depositions and download statistics | metadata CC0 |
| [Bioconductor](https://bioconductor.org/packages/stats/) | package downloads and distinct IPs | courtesy statistics files, no stated licence |
| [ecosyste.ms](https://ecosyste.ms) | package discovery and cross-registry downloads | CC-BY-SA 4.0 |
| [GitHub](https://docs.github.com/en/graphql) | repositories, releases and tags | GitHub API terms |
| [Research Software Directory](https://research-software-directory.org) | literature mentions of software | Apache-2.0 platform, CC-BY content |
| [WikiPathways SPARQL](https://sparql.wikipathways.org) | pathway and species counts | CC0 |
| [Maastricht University Pure](https://cris.maastrichtuniversity.nl) | department roster | institutional CRIS |

Only derived aggregates are republished here, never a verbatim copy of a third-party
dataset. Where a source publishes no licence for its statistics, the figures are shown
with a link back rather than redistributed.

## Vendored libraries

Charts are drawn with Vega-Lite, vendored into this repository and pinned rather than
loaded from a content delivery network, so the page renders identically in five years
and can be archived intact.

| File | Version | SHA-384 |
|---|---|---|
| `vega.min.js` | 5.30.0 | `em7CHpJd+SsMugVFf6TY7AKQcLWMcbPhD84hmNK8o6WFDkK+2uHSUQRVQV1/w827` |
| `vega-lite.min.js` | 5.21.0 | `GhkD6ks9/zgY1m5EFOUZWz/vMVMUFF/92DL61RZc+B42J8osL+jNufKv68bNHHZ2` |
| `vega-embed.min.js` | 6.26.0 | `TqXb8su49m5OnEpKGO8m+VrgHesrUxyP22HgpXi4hnh1Hm43dXroiSYemNf5D8lv` |
