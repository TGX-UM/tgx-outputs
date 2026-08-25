"""Command line: collect | derive | build | doctor."""

from __future__ import annotations

import argparse
import json
import sys

from . import config as cfg
from . import guards, store
from .collect import COLLECTORS, run_all
from .derive import freshness, tables, whats_new
from .http import HttpClient


def cmd_collect(args: argparse.Namespace) -> int:
    only = args.only.split(",") if args.only else None
    mode = "replay" if args.replay else ("record" if args.record else "live")
    semantics = cfg.semantics()
    previous = store.previous_values()

    with HttpClient(mode=mode, max_calls=args.max_calls) as http:
        envelopes = run_all(http, only=only, on_start=lambda n: print(f"  … {n}", flush=True))

    promoted: dict[str, list] = {}
    quarantine: dict[str, list] = {}
    for name, env in envelopes.items():
        if env.status == "skipped":
            promoted[name] = []
            continue
        guards.check_volume(env, store.volume_history(name))
        if env.status == "failed":
            promoted[name] = []
            continue
        keep, dropped = guards.check_records(env, semantics, previous)
        env.records = keep
        guards.check_empty(env)
        promoted[name] = keep
        quarantine[name] = dropped

    snap_path, man_path = store.write_run(envelopes, quarantine, promoted)

    print()
    for name, env in sorted(envelopes.items()):
        mark = {"ok": "ok      ", "degraded": "DEGRADED", "failed": "FAILED  ",
                "skipped": "skipped "}[env.status]
        q = len(quarantine.get(name, []))
        print(f"  {mark} {name:<14} {len(promoted[name]):>5} records"
              + (f"  ({q} quarantined)" if q else ""))
        for err in env.errors[:2]:
            print(f"           ↳ {err.splitlines()[0][:110]}")
    print(f"\n  snapshot → {snap_path.relative_to(cfg.ROOT)}")
    print(f"  manifest → {man_path.relative_to(cfg.ROOT)}")

    if any(e.status == "failed" for e in envelopes.values()):
        return 1
    return 0


def cmd_derive(args: argparse.Namespace) -> int:
    snapshot = store.load_latest()
    out = cfg.DOCS_DIR / "data"
    written = tables.write_long(snapshot, out)
    fresh = freshness.assess(snapshot)
    snaps = sorted(store.snapshot_dir().glob("*.json"))
    prev = json.loads(snaps[-2].read_text()) if len(snaps) > 1 else None
    changes = whats_new.diff(snapshot, prev)

    (cfg.DATA_DIR / "derived").mkdir(parents=True, exist_ok=True)
    (cfg.DATA_DIR / "derived" / "freshness.json").write_text(json.dumps(fresh, indent=1))
    (cfg.DATA_DIR / "derived" / "whats_new.json").write_text(json.dumps(changes, indent=1))

    print(f"  {len(written) - 1} metric CSVs → {out.relative_to(cfg.ROOT)}")
    print(f"  freshness: {fresh['summary']}")
    print(f"  changes since previous run: {len(changes)}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    from .site.build import build

    return build()


def cmd_doctor(args: argparse.Namespace) -> int:
    """Validate config and report what a run would cost, without calling anything."""
    problems: list[str] = []
    semantics = cfg.semantics()

    required = {"label", "counts", "source", "cumulative", "granularity", "caveat"}
    for name, spec in semantics.items():
        missing = required - set(spec)
        if missing:
            problems.append(f"metric {name}: missing {sorted(missing)}")
        if spec.get("cumulative") and spec.get("granularity") != "none":
            problems.append(
                f"metric {name}: cumulative metrics must be granularity:none "
                f"(a level cannot belong to a period)")

    orcids = cfg.roster()
    for o in orcids:
        if len(o) != 19 or o.count("-") != 3:
            problems.append(f"roster: {o!r} is not a well-formed ORCID")

    known = set(COLLECTORS)
    for name in cfg.sources().get("collectors", {}):
        if name not in known:
            problems.append(f"collectors: {name!r} is configured but not implemented")
    for name in known:
        if name not in cfg.sources().get("collectors", {}):
            problems.append(f"collectors: {name!r} is implemented but not configured")

    enabled = [n for n in known if cfg.collector_enabled(n)]
    print(f"  config sha        {cfg.config_sha()}")
    print(f"  roster            {len(orcids)} ORCIDs")
    print(f"  metrics defined   {len(semantics)}")
    print(f"  orgs              {len(cfg.sources().get('github_orgs', []))}")
    print(f"  collectors        {len(enabled)} enabled of {len(known)}: {', '.join(sorted(enabled))}")
    print("  secrets required  none (GITHUB_TOKEN optional, OPENALEX_API_KEY optional)")

    if problems:
        print("\n  problems:")
        for p in problems:
            print(f"    ✗ {p}")
        return 1
    print("\n  ✓ config is consistent")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tgx", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("collect", help="fetch every enabled source")
    c.add_argument("--only", help="comma-separated collector names")
    c.add_argument("--replay", action="store_true", help="use recorded fixtures, no network")
    c.add_argument("--record", action="store_true", help="save responses as fixtures")
    c.add_argument("--max-calls", type=int, default=None, help="hard call budget")
    c.set_defaults(func=cmd_collect)

    d = sub.add_parser("derive", help="turn the snapshot into CSVs and page data")
    d.set_defaults(func=cmd_derive)

    b = sub.add_parser("build", help="generate the site's markdown and charts")
    b.set_defaults(func=cmd_build)

    doc = sub.add_parser("doctor", help="validate config; makes no network calls")
    doc.set_defaults(func=cmd_doctor)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
