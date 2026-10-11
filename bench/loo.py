#!/usr/bin/env python3
"""Leave-one-out (TASK-18): disable each rule that fired in a full run on its own and judge it:

    uv run --project bench python bench/loo.py [--baseline <run>] [--guard tab]

Writes <data>/loo/<time>/mutations/*.toml (one per rule), results.json and report.md (bench/mutate.py's format):
an accepted removal is a candidate; the rejected ones at the bottom are the rules that earn their place.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from maisecrets_bench import loo, mutate, mutation, run, setup
from maisecrets_bench.paths import BenchError, data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=Path, help="a full run directory (default: the newest full run)")
    ap.add_argument("--guard", default="", help="comma-separated datasets that must not get worse, without weight")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--recall-tolerance", type=float, default=100 * mutation.RECALL_TOLERANCE,
                    help="recall points a dataset may lose when its score does not fall (default %(default).1f)")
    args = ap.parse_args(argv)
    out = data_dir() / "loo" / time.strftime("%Y%m%d-%H%M%S")
    try:
        manifest = json.loads((setup.default_out() / "manifest.json").read_text(encoding="utf-8"))
        base_dir = args.baseline or run.newest_full_run(data_dir() / "runs", manifest)
        samples, det, names = mutate.baseline(base_dir, setup.default_out())
        roles = {**run.default_roles(names), **{n: "guard" for n in args.guard.split(",") if n}}
        muts = loo.mutations(json.loads((base_dir / "metrics.json").read_text(encoding="utf-8")))
        loo.write(muts, out / "mutations")
        print(f"{len(muts)} rules fired in {base_dir.name}; judging each one left out", flush=True)
        results = mutate.evaluate(muts, samples, det, roles, args.jobs, args.recall_tolerance / 100)
    except (BenchError, ValueError) as exc:
        print(f"loo: {exc}", file=sys.stderr)
        return 1
    (out / "results.json").write_text(json.dumps({"baseline": str(base_dir), "roles": roles, "results": results},
                                                 indent=2, default=str) + "\n", encoding="utf-8")
    text = mutate.report(results, base_dir, args.recall_tolerance / 100)
    (out / "report.md").write_text(text, encoding="utf-8")
    print(text.split("\n## ")[0])
    print(f"report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
