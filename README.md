# TGX Outputs

**[tgx-um.github.io/tgx-outputs](https://tgx-um.github.io/tgx-outputs/)**

What the Department of Translational Genomics at Maastricht University publishes,
ships and maintains — collected automatically from public sources once a week and
published as a static page.

The department's output is spread across a dozen GitHub organisations, several package
registries, a handful of SPARQL endpoints and a few hundred Zenodo depositions. Nobody
could previously answer "what did TGX ship this year" without a week of digging, and
annual reports, grant renewals and consortium reviews all need that answer.

## What this is not

It is **not** a measure of individuals. There are no per-person pages, counts or
rankings, and there never will be — ORCIDs are used as a query key and nothing else.
See [what we deliberately do not show](docs/not-shown.md) for the full list and the
reasoning behind each omission.

It is also not service monitoring. Whether the department's endpoints are up right now
is a different job with a different cadence, and the cluster already has monitoring for it.

## How it works

```
config/projects.yml  →  collectors  →  data/snapshots/*.json  →  docs/data/*.csv  →  static site
(the list of things      (one file      (whole state per run,     (every figure's
 being tracked)           per source)    on the `data` branch)     download link)
```

One file lists the projects. Adding one is a block of YAML and a pull request.

Once a week a GitHub Actions job collects every source, checks the results against a
set of integrity rules, writes a complete snapshot, and rebuilds and deploys the site
in the same job. No database, no server, no stored credential.

**Everything runs on public data with no secrets.** That is enforced by a test, not by
convention — see `tests/test_no_secrets_required.py`.

## Working on it

```bash
make install     # into a virtualenv
make check       # config validation, lint, offline tests
make offline     # build the entire site from fixtures, no network, no credentials
make serve       # http://localhost:8000
```

`make offline` is the one that matters. If it passes, the project can be forked, handed
over, and rebuilt in five years.

## Changing what is tracked

Everything a human edits lives in `config/`, and each file is validated against a JSON
schema in CI, so a malformed change fails the pull request rather than the next refresh:

| To do this | Edit |
|---|---|
| Track another project | `config/projects.yml`, then `tgx doctor --projects` |
| Add or remove an ORCID | `config/roster.yml` (publications page only) |
| Leave something out | `config/exclusions.yml`; a reason is required and is published |
| Add a number to the page | `config/metric_semantics.yml` first, or it will not render |

To be excluded from the underlying queries, open an issue or email the address in
`config/sources.yml`. No reason is needed and none will be asked for.

## Numbers that look wrong

They may well be. Every figure links to the CSV behind it and shows the exact source
and collection date, and the run manifests on the `data` branch record what each source
returned, what failed and what was quarantined.
[Open an issue](https://github.com/TGX-UM/tgx-outputs/issues/new) — see
[`RUNBOOK.md`](RUNBOOK.md) for what to do when a collector breaks.

## Prior art

Modelled on [RECETOX/specdatri_reporting](https://github.com/RECETOX/specdatri_reporting),
with its failure modes turned into tests. The
[Research Software Directory](https://research-software-directory.org) already tracks
much of this department's software and computes literature mentions for it; this project
consumes that rather than rebuilding it.

## Licence

Code MIT. Figures are derived aggregates of public data — see
[`ATTRIBUTION.md`](ATTRIBUTION.md), which lists every source and its terms.
