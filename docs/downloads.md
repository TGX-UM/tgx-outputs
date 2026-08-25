# Download the data

Every figure links to the CSV behind it, and they are all here. Long format:
`metric, entity, period, value, partial, collected_on`. One row per observation.

- [Everything, one file](data/all_metrics.csv)

Individual metrics are at `data/<metric>.csv`; the names are in the
[indicator catalogue](methodology.md#indicator-catalogue).

## Raw snapshots

Each run writes a full snapshot and a manifest to the `data` branch:

- `snapshots/<date>.json` holds everything true that day
- `manifests/<date>.json`, per-source status, errors, quarantined records, calls made

Whole state per run rather than a chain of diffs, so one file can be read on its own.

## Reuse

Code is MIT. Figures are derived aggregates of public data; see the
[attribution table](methodology.md#sources). Where a source sets terms, those terms
travel with it.
