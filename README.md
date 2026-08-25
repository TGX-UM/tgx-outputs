# TGX Outputs

**[tgx-um.github.io/tgx-outputs](https://tgx-um.github.io/tgx-outputs/)**

The software, data resources and services the Department of Translational Genomics at
Maastricht University builds — collected automatically from public sources once a week
and published as a static page.

That output is spread across a dozen GitHub organisations, several package registries,
a handful of SPARQL endpoints and a set of deposited datasets. Nobody could previously
answer "what did TGX ship this year" without a week of digging, and annual reports,
grant renewals and consortium reviews all need that answer.

## What this is not

It is **not** a bibliometric dashboard. The department's publication record lives in
Pure and is reported from there; duplicating it here would only produce a second set of
books that disagrees with the first. What this tracks is software: repositories,
releases, packages, containers, running services, and the citations of the papers that
describe each tool.

It is **not** a measure of individuals. There are no per-person pages, counts or
rankings, and there never will be — no person is queried and no ORCID is stored. Nor
are there stars, forks, h-indices or journal rankings: every figure names what it
counts and what it does not mean, and the methodology page carries both.

It is also not service monitoring. Whether the department's endpoints are up right now
is a different job with a different cadence, and the cluster already has monitoring for it.

## How it works

```mermaid
flowchart LR
    subgraph edit["config/ (the only files a person edits)"]
        direction TB
        proj["<b>projects.yml</b><br/>repos · packages · docker<br/>ghcr · rsd · papers · probes"]
        sem["<b>metric_semantics.yml</b><br/>what each number counts"]
        exc["<b>exclusions.yml</b><br/>what is left out, and why"]
    end

    subgraph coll["collectors (read public APIs, no credentials)"]
        direction TB
        tools["<b>per project</b><br/>github · ecosystems · bioconductor<br/>dockerhub · ghcr · rsd<br/>citations · services"]
    end

    proj --> tools
    tools --> guards{{guards}}
    sem -. "no definition,<br/>no figure" .-> guards
    exc -. "and the reason<br/>gets published" .-> guards

    guards -- "fails a rule" --> quar["quarantined in the run<br/>manifest, never published"]
    guards -- passes --> snap[("data branch<br/>one whole-state<br/>snapshot per run")]
    snap --> csv["docs/data/*.csv<br/>one file per metric"]
    csv --> build["build"]
    sem -. "labels and caveats" .-> build
    build --> site["GitHub Pages"]

    classDef cfg fill:#3d6fb422,stroke:#3d6fb4,color:#000
    classDef gate fill:#c26a3a22,stroke:#c26a3a,color:#000
    classDef out fill:#4a8a7222,stroke:#4a8a72,color:#000
    class proj,sem,exc cfg
    class guards,quar gate
    class snap,csv,site out
```

One GitHub Actions job, weekly, does the whole run: collect, check, build, deploy, then
commit the snapshot. Deploying in the same job is deliberate — a push made with
`GITHUB_TOKEN` does not trigger another workflow, which is how the project this one is
modelled on served a two-month-old page while every run showed green.

Three properties hold by construction, and each has a test:

- **Nothing is published without a definition.** A metric absent from
  `metric_semantics.yml` does not render, and the methodology page is generated from
  that same file, so a definition cannot drift from the figure it describes.
- **A failed source reads as "not collected", never as 0.** Summing the records of a
  source that returned nothing gives zero, and a tile then states it as fact.
- **No stored credentials.** Every source is public. `tests/test_no_secrets_required.py`
  fails if that stops being true.

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
| Leave something out | `config/exclusions.yml`; a reason is required and is published |
| Add a number to the page | `config/metric_semantics.yml` first, or it will not render |

To have a project, repository, package or DOI excluded from the queries, open an issue
or email the address in `config/sources.yml`. No reason is needed and none will be
asked for.

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
