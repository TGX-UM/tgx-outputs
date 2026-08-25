# Contributing

Almost every useful change is one block in one file. No Python needed.

## Add a project

Copy a block in `config/projects.yml`, change the values, open a pull request. That
file explains every field at the top. Only `id`, `name` and `what` are required; leave
out anything the project does not have and nothing about it is shown.

```yaml
  - id: my-tool
    name: My Tool
    what: One sentence a stranger would understand.
    repos: [someorg/my-tool]
    packages: [pypi.org/my-tool]
    docker: [somenamespace/my-tool]
    ghcr: [someowner/my-tool]
    rsd: [my-tool]
```

Then check the identifiers actually resolve:

```bash
tgx doctor --projects
```

It calls each API and tells you which ones do not exist. CI runs the same check.

If a tool is not in the Research Software Directory, register it there rather than
worrying about the `rsd` field. That is where the literature mention counts come from,
and it is maintained by someone else.

## Leave something out

`config/exclusions.yml`, by repository, package or DOI. A reason is required and is
published on the methodology page, because an undeclared omission looks the same as a
bug. To have something removed, open an issue or email the contact in
`config/sources.yml`; no reason needed.

## Add a number to the page

1. Define it in `config/metric_semantics.yml` first: what one unit counts, whether it
   is a running total or a per-period count, and what it does not mean. Nothing renders
   without this, and the methodology page is generated from it.
2. Emit it from a collector in `src/tgx_outputs/collect/`.
3. Add a chart in `src/tgx_outputs/site/charts.py` and reference it from a page.
4. `make record`, then `make check` and `make offline`.

## Ground rules

- Nothing about individuals. No per-person figures or rankings, and no person is
  queried: every target is a repository, package, image, endpoint or DOI.
- Software, not bibliometrics. The department's publication record lives in Pure; the
  only citations here are of the papers that describe a tracked tool.
- Every number carries a caveat. If you cannot say what it does not mean, it is not
  ready to publish.
- A running total is never stored against a period.
- No stored secrets. A test enforces it.
- `make offline` must pass. That is what keeps this maintainable by whoever comes next.
