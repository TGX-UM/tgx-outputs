---
hide:
  - toc
---

# Overview

The software and data resources of the Department of Translational Genomics, collected
once a week from public sources.

--8<-- "freshness.md"

--8<-- "cards.md"

--8<-- "projects.md"

## Releases { #releases }

--8<-- "fig_releases_by_year.md"

## Downloads { #downloads }

Each registry counts over its own window, and the two are never added together.

--8<-- "fig_downloads_lifetime.md"

--8<-- "fig_downloads_recent.md"

--8<-- "fig_bioc_ips.md"

## Citations { #citations }

--8<-- "fig_citations.md"

### Software mentions

--8<-- "fig_rsd_mentions.md"

## Containers { #containers }

--8<-- "fig_docker_pulls.md"

---

To add a project, add a row to
[`config/projects.csv`](https://github.com/TGX-UM/tgx-outputs/blob/main/config/projects.csv).
[`config/README.md`](https://github.com/TGX-UM/tgx-outputs/blob/main/config/README.md)
explains the columns, and `tgx doctor --projects` checks the identifiers resolve.
