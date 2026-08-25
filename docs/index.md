# TGX tools

The software and data resources this department builds. Refreshed weekly from public
sources.

--8<-- "freshness.md"

--8<-- "cards.md"

--8<-- "projects.md"

## What changed since the last refresh

--8<-- "whats_new.md"

## Releases { #releases }

--8<-- "fig_releases_by_year.md"

## Downloads { #downloads }

--8<-- "fig_bioc_ips.md"

## Citations { #citations }

Citations of the papers that describe each tool, every update paper counted.
WikiPathways has six, spanning 2012 to 2024, and people cite whichever was current when
they did the work.

--8<-- "fig_citations.md"

### Software mentions

A different and much smaller measure: software named in a paper's text, from a
text-mining dataset the Research Software Directory carries. It is badly incomplete,
reporting 6 for rWikiPathways against thousands of citations. Shown because it counts
use that never turns into a citation, not because the number is right.

--8<-- "fig_rsd_mentions.md"

## Services we run { #services }

BridgeDb and WikiPathways are web services and web sites as much as they are packages.
What is counted here is what the department builds for them: the mapping databases,
and the RDF layer behind the endpoints. The pathway and AOP content those endpoints
carry is curated by international communities and is not counted as our output.

--8<-- "fig_service_scale.md"

--8<-- "fig_dataset_downloads.md"

## Containers { #containers }

--8<-- "fig_docker_pulls.md"

--8<-- "fig_ghcr_tags.md"

---

To add a project, copy a block in
[`config/projects.yml`](https://github.com/TGX-UM/tgx-outputs/blob/main/config/projects.yml)
and open a pull request. The file explains each field, and `tgx doctor --projects`
checks the identifiers resolve. No code changes needed.
