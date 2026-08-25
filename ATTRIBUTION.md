# Sources and attribution

This project republishes **derived aggregates** of public data, never a verbatim copy
of a third-party dataset. Where a source publishes no licence for its statistics, the
figures are shown with a link back rather than redistributed.

| Source | Used for | Terms |
|---|---|---|
| [OpenAlex](https://openalex.org) | citations of the papers describing each tool | CC0 |
| [Zenodo](https://zenodo.org) | dataset download statistics, read per record by DOI | metadata CC0 |
| [Bioconductor](https://bioconductor.org/packages/stats/) | package downloads, distinct IPs, rank | courtesy statistics files with **no stated licence** — aggregates only, with attribution |
| [ecosyste.ms](https://ecosyste.ms) | package discovery, cross-registry downloads | CC-BY-SA 4.0 |
| [GitHub](https://docs.github.com/en/graphql) | repositories, releases, tags | GitHub API terms of service |
| [Research Software Directory](https://research-software-directory.org) | literature mentions of software | platform Apache-2.0, content CC-BY |
| [Docker Hub](https://hub.docker.com) | image pulls | Docker terms of service |
| [GitHub Container Registry](https://ghcr.io) | tags published | GitHub terms of service |
| [WikiPathways SPARQL](https://sparql.wikipathways.org) | pathway and species counts | CC0 |

The TGX logo and icon in `docs/assets/images/` are the department's own marks, used on
the department's own page. The site follows the UM house style: `#001C3D` UM Blue,
links `#1E5A96` turning `#D2460F` on hover, headings at weight 600. Dark mode is an
extension rather than a quotation — the house style documents none — and lightens those
two colours until they clear a dark ground.

Type is [Open Sans](https://fonts.google.com/specimen/Open+Sans) (Apache-2.0), which is
the substitute UM's own web guidance names for Thesis Sans, the licensed house typeface.
The four subset faces in `docs/assets/fonts/` are served from this repository rather
than from Google Fonts, so the page makes no third-party request; the licence ships
alongside them.

Charts are drawn with [Vega-Lite](https://vega.github.io/vega-lite/) (BSD-3-Clause),
vendored into `docs/assets/js/` and pinned; versions and SHA-384 hashes are listed on
the site's methodology page. The overview tiles use inline SVG from
[Simple Icons](https://simpleicons.org) (CC0-1.0) and
[Octicons](https://primer.style/octicons) (MIT), vendored into
`src/tgx_outputs/site/icons.py`; the brand marks remain the property of their owners and
are used only to identify the registry a figure comes from. The site is built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) (MIT).

If you maintain one of these services and would rather this project used your data
differently, please open an issue.
