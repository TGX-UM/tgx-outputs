# Contributing

Most useful changes are one line in one file, and need no Python.

## Add or remove an ORCID

Edit `config/roster.yml`. ORCIDs only — no names, no roles, no dates. That file is
public and, once committed, is permanently archived by third parties, which is why it
holds nothing else.

**To be left out entirely**, add your ORCID to `config/exclusions.yml` with a reason of
your choosing (`"requested"` is enough), or just email the address in
`config/sources.yml` and someone will do it. You do not have to justify it.

## Track another organisation, repository or package

`config/sources.yml`. Organisations need an attribution band:

| Band | Meaning |
|---|---|
| `tgx` | The department's own organisation |
| `heritage` | The department under its former name, BiGCaT |
| `community` | Resources co-maintained with other institutions |
| `consortium` | Project organisations the department participates in |

Bands are never added together on the page without a qualifier — "TGX produced 430
repositories" is not a defensible claim, and the bands are what stop the page making it.

Most packages are discovered automatically from repository URLs, so `packages_seed` is
only for things that discovery misses.

## Leave something out

`config/exclusions.yml`. A reason is required, and it is published on the methodology
page. That is deliberate: an undeclared omission is indistinguishable from a bug.

## Add a number to the page

1. Define it in `config/metric_semantics.yml` **first** — label, what one unit of it
   counts, its source, whether it is a level or a per-period count, and what it does
   *not* mean. The build refuses to render anything undefined, and the methodology page
   is generated from this file, so a definition cannot drift from the figure.
2. Emit it from a collector in `src/tgx_outputs/collect/`.
3. Add a chart spec in `src/tgx_outputs/site/charts.py` and include it in a page.
4. `make record` to capture fixtures, then `make check` and `make offline`.

Before proposing one, read [what we deliberately do not show](docs/not-shown.md). Some
metrics are absent on purpose.

## Ground rules

- **Nothing about individuals.** No per-person figures, pages or rankings.
- **Every number carries a caveat.** If you cannot write what it does not mean, it is
  not ready to publish.
- **A level is not a flow.** An all-time counter must never be stored against a period.
- **No stored secrets.** Everything runs on public data; a test enforces it.
- **`make offline` must pass.** It is what keeps this maintainable by whoever comes next.
