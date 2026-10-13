#!/usr/bin/env python3
"""Score the detection rules on the benchmark data (docs/BENCHMARK.md). Run from the repository root after setup:

    uv run --project bench python bench/run.py                    # every dataset in the manifest
    uv run --project bench python bench/run.py --only gretel --limit 2000

Writes <data>/runs/<time>/metrics.json and report.md: counts, rates and rule ids, never a value.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from maisecrets_bench import run, setup
from maisecrets_bench.paths import BenchError, data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated datasets (default: all in the manifest)")
    ap.add_argument("--limit", type=int, help="a fixed random sample of at most this many samples per dataset")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args(argv)
    try:
        parquet = setup.default_out()
        manifest_path = parquet / "manifest.json"
        if not manifest_path.exists():
            raise BenchError(f"no benchmark data in {parquet}; run bench/setup.py first")
        known = sorted(json.loads(manifest_path.read_text(encoding="utf-8"))["datasets"])
        names = args.only.split(",") if args.only else run.default_datasets(
            json.loads(manifest_path.read_text(encoding="utf-8")))
        missing = set(names) - set(known)
        if missing:
            raise BenchError(f"not set up: {', '.join(sorted(missing))}")
        out = data_dir() / "runs" / time.strftime("%Y%m%d-%H%M%S")
        summary = run.run(parquet, names, out, args.jobs, args.limit)
    except BenchError as exc:
        print(f"run: {exc}", file=sys.stderr)
        return 1
    for name, s in summary["scores"].items():
        print(f"{name:10} score {100 * s:.1f}%")
    overall = summary["overall"]   # None when every dataset of the run is a guard (no weight in the mean)
    print(f"overall    {'-' if overall is None else f'{100 * overall:.1f}%'}   report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
