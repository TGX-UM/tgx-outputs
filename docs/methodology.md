# How the numbers are made

Everything comes from public APIs, collected weekly by a job in
[this repository](https://github.com/TGX-UM/tgx-outputs). No manual data entry, no
database, and no credential beyond the token GitHub issues to its own workflow.

## What counts as TGX

The tracked list is [`config/projects.yml`](https://github.com/TGX-UM/tgx-outputs/blob/main/config/projects.yml):
software and data resources the department builds or co-maintains, each named
explicitly with the repositories, packages, images, endpoints and papers that belong to
it. Nothing is discovered by matching a person, an affiliation string or an ORCID, so
nothing arrives in a figure because a name looked right.

No person is queried and none is stored. The department's publication record is a
separate thing, held in Pure, and this page does not reproduce it.

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

What is republished here are derived aggregates, never a verbatim copy of anyone's
dataset. Where a source publishes no licence for its statistics, the figure is shown
with a link back rather than redistributed.

| Source | Used for | Terms |
|---|---|---|
| [OpenAlex](https://openalex.org) | citations of the papers describing each tool | CC0 |
| [Zenodo](https://zenodo.org) | dataset download statistics, read per record by DOI | metadata CC0 |
| [Bioconductor](https://bioconductor.org/packages/stats/) | package downloads, distinct IPs, rank | courtesy statistics files with **no stated licence**; aggregates only, with attribution |
| [ecosyste.ms](https://ecosyste.ms) | package discovery, cross-registry downloads | CC-BY-SA 4.0 |
| [GitHub](https://docs.github.com/en/graphql) | repositories, releases, tags | GitHub API terms of service |
| [Research Software Directory](https://research-software-directory.org) | literature mentions of software | platform Apache-2.0, content CC-BY |
| [Docker Hub](https://hub.docker.com) | image pulls | Docker terms of service |
| [GitHub Container Registry](https://ghcr.io) | tags published | GitHub terms of service |

If you maintain one of these services and would rather this project used your data
differently, please [open an issue](https://github.com/TGX-UM/tgx-outputs/issues/new).

## Charts and icons

Charts are drawn with [Vega-Lite](https://vega.github.io/vega-lite/) (BSD-3-Clause),
vendored into `docs/assets/js/` and pinned rather than loaded from a CDN, so the page
renders the same in five years and archives intact. The site itself is built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) (MIT).

The type and the icons work the same way. [Open Sans](https://fonts.google.com/specimen/Open+Sans)
(Apache-2.0) is the substitute UM's own web guidance names for Thesis Sans, its licensed
house typeface; the four subset faces are served from this repository, licence included.
The tile icons are inline SVG taken from [Simple Icons](https://simpleicons.org)
(CC0-1.0) and [Octicons](https://primer.style/octicons) (MIT); the brand marks belong to
their owners, and they are there to say which registry a number came from. The project
logos work the same way: each is the mark that project publishes in its own repository,
copied into `docs/assets/images/logos/` so the page fetches nothing, and shown only to
identify the tool whose figures sit beneath it. Every one of them remains the property
of the project that made it. A project with no mark of its own gets initials instead.
Nothing on this page is requested from anyone else.

The TGX logo and icon are the department's own marks. Colours follow the UM house style,
and the chart series take the department's own `#00A2DB` and `#E84E10`.

| File | Version | SHA-384 |
|---|---|---|
| `vega.min.js` | 5.30.0 | `em7CHpJd+SsMugVFf6TY7AKQcLWMcbPhD84hmNK8o6WFDkK+2uHSUQRVQV1/w827` |
| `vega-lite.min.js` | 5.21.0 | `GhkD6ks9/zgY1m5EFOUZWz/vMVMUFF/92DL61RZc+B42J8osL+jNufKv68bNHHZ2` |
| `vega-embed.min.js` | 6.26.0 | `TqXb8su49m5OnEpKGO8m+VrgHesrUxyP22HgpXi4hnh1Hm43dXroiSYemNf5D8lv` |
