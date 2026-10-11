#!/usr/bin/env python3
"""Judge rule mutations against a saved full run (docs/BENCHMARK.md, Judging a change):

    uv run --project bench python bench/mutate.py bench/mutations/*.toml [--baseline <run>] [--guard tab]

Writes <data>/mutations/<time>/report.md and results.json: each mutation accepted or rejected, ranked by the change
of the mean score of the scored datasets. A --guard dataset must not get worse but has no weight in the mean.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from maisecrets_bench import mutate, mutation, setup
from maisecrets_bench.paths import BenchError, data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mutations", nargs="+", type=Path)
    ap.add_argument("--baseline", type=Path, help="a full run directory (default: the newest full run)")
    ap.add_argument("--guard", default="", help="comma-separated datasets that must not get worse, without weight")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args(argv)
    try:
        if args.baseline:
            base_dir = args.baseline
        else:
            full = [p.parent for p in sorted((data_dir() / "runs").glob("*/datasets.json"))
                    if not json.loads(p.read_text(encoding="utf-8")).get("limit")]
            if not full:
                raise BenchError("no full run to compare with; run bench/run.py first")
            base_dir = full[-1]
        samples, det, names = mutate.baseline(base_dir, setup.default_out())
        roles = {n: "guard" for n in args.guard.split(",") if n}
        unknown = set(roles) - set(names)
        if unknown:
            raise BenchError(f"--guard names datasets not in the baseline: {', '.join(sorted(unknown))}")
        muts = [mutation.load(p) for p in args.mutations]
        results = mutate.evaluate(muts, samples, det, roles, args.jobs)
    except (BenchError, ValueError) as exc:
        print(f"mutate: {exc}", file=sys.stderr)
        return 1
    out = data_dir() / "mutations" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"baseline": str(base_dir), "roles": roles, "results": results},
                                                 indent=2, default=str) + "\n", encoding="utf-8")
    text = mutate.report(results, base_dir)
    (out / "report.md").write_text(text, encoding="utf-8")
    print(text.split("\n## ")[0])
    print(f"report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
