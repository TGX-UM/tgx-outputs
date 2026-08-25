# Sources and attribution

This project republishes **derived aggregates** of public data, never a verbatim copy
of a third-party dataset. Where a source publishes no licence for its statistics, the
figures are shown with a link back rather than redistributed.

| Source | Used for | Terms |
|---|---|---|
| [OpenAlex](https://openalex.org) | publications, open access, citations, collaboration | CC0 |
| [Crossref](https://www.crossref.org) | coverage comparison | CC0 |
| [Europe PMC](https://europepmc.org) | coverage comparison | EMBL-EBI terms of use |
| [PubMed / NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) | coverage comparison | NCBI usage policy; requests identify a tool and contact address |
| [Zenodo](https://zenodo.org) | depositions, download statistics | metadata CC0 |
| [Bioconductor](https://bioconductor.org/packages/stats/) | package downloads, distinct IPs, rank | courtesy statistics files with **no stated licence** — aggregates only, with attribution |
| [ecosyste.ms](https://ecosyste.ms) | package discovery, cross-registry downloads | CC-BY-SA 4.0 |
| [GitHub](https://docs.github.com/en/graphql) | repositories, releases, tags | GitHub API terms of service |
| [Research Software Directory](https://research-software-directory.org) | literature mentions of software | platform Apache-2.0, content CC-BY |
| [WikiPathways SPARQL](https://sparql.wikipathways.org) | pathway and species counts | CC0 |
| [Maastricht University Pure](https://cris.maastrichtuniversity.nl) | department roster (ORCIDs only) | institutional CRIS, OpenAIRE CERIF profile |

Charts are drawn with [Vega-Lite](https://vega.github.io/vega-lite/) (BSD-3-Clause),
vendored into `docs/assets/js/` and pinned; versions and SHA-384 hashes are listed on
the site's methodology page. The site is built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) (MIT).

If you maintain one of these services and would rather this project used your data
differently, please open an issue.
