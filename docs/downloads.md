# Download the data

Every figure on this site is backed by a CSV, and all of them are published here. The
chart and the download are the same file — they cannot disagree.

The format is long, not wide: `metric, entity, period, value, partial, collected_on`.
One row per observation. A wide matrix with a column per package rewrites its own
header whenever something is added or removed, which makes the file history unreadable.

- **[Everything, one file](data/all_metrics.csv)**

Individual metrics are at `data/<metric>.csv` — the name is shown in the
[indicator catalogue](methodology.md#indicator-catalogue), and each figure links
directly to its own.

## Raw snapshots

Each weekly run writes a complete snapshot and a manifest to the `data` branch of the
repository:

- `snapshots/<date>.json` — everything that was true that day
- `manifests/<date>.json` — per-source status, errors, quarantined records, and the
  list of calls made

Whole state per run, rather than a chain of diffs, so any single file can be opened and
read on its own without replaying history.

## Reuse

The code is MIT. The figures are derived aggregates of public data from the sources
listed in the [attribution table](methodology.md#sources-and-attribution); where a
source sets terms on its data, those terms travel with it. If you use these numbers,
please link back to this page so a reader can see how they were made.
