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

Registries do not count the same thing. Bioconductor and CRAN publish a lifetime total;
npm and PyPI publish only a rolling 30-day figure. Both are shown, each labelled with
its own window, and they are never added together.

--8<-- "fig_bioc_ips.md"

## Citations { #citations }

Citations of the papers that describe each tool, every update paper counted.
WikiPathways has six, spanning 2012 to 2024, and people cite whichever was current when
they did the work.

--8<-- "fig_citations.md"

### Software mentions

A much smaller and weaker measure: software named in a paper's text, from a text-mining
dataset the Research Software Directory carries. It is badly incomplete. For
rWikiPathways it reports 6, against thousands of citations. It is here because it
catches use that never becomes a citation, and for no other reason.

--8<-- "fig_rsd_mentions.md"

## Services we run { #services }

BridgeDb and WikiPathways are web services and web sites as much as they are packages,
and a page showing only releases and downloads undersells them. What we count is what
the department builds for them: the mapping databases, and the RDF layer behind the
endpoints. The pathway and AOP content those endpoints serve belongs to the
international communities who curate it, and none of it is counted here.

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
