---
hide:
  - toc
---

# What we build

The software and data resources of the Department of Translational Genomics, collected
once a week from public sources.

--8<-- "freshness.md"

--8<-- "cards.md"

--8<-- "projects.md"

## Releases { #releases }

--8<-- "fig_releases_by_year.md"

## Downloads { #downloads }

Registries do not count the same thing. Bioconductor and CRAN publish a lifetime total;
npm and PyPI publish only a rolling 30-day figure. Both are shown, each labelled with
its own window, and they are never added together. Each registry keeps its own panel
for the same reason: the registry is what did the counting, not a kind of package.

--8<-- "fig_downloads_lifetime.md"

--8<-- "fig_downloads_recent.md"

Bioconductor is the one registry that publishes a monthly series rather than a single
number, so it is the only place a trend can be drawn at all.

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

## Containers { #containers }

--8<-- "fig_docker_pulls.md"

---

To add a project, copy a block in
[`config/projects.csv`](https://github.com/TGX-UM/tgx-outputs/blob/main/config/projects.csv)
and open a pull request. The file explains each field, and `tgx doctor --projects`
checks the identifiers resolve. No code changes needed.
