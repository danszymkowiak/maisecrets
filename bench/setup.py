#!/usr/bin/env python3
"""Fetch and normalise the benchmark datasets (docs/BENCHMARK.md). Run from the repository root:

    uv run --project bench python bench/setup.py --creddata ../CredData [--tab ../text-anonymization-benchmark]
    uv run --project bench python bench/setup.py --only gretel,tab

Without --creddata, CredData is skipped (its download takes hours; the message says how). Without --tab, TAB is
cloned into the data directory. The data goes to $MAISECRETS_BENCH_DATA (default ~/.cache/maisecrets-bench).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maisecrets_bench import setup
from maisecrets_bench.paths import BenchError, data_dir

DATASETS = ("creddata", "tab", "gretel")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--creddata", type=Path, help="a CredData checkout after its download_data.py")
    ap.add_argument("--tab", type=Path, help="a text-anonymization-benchmark checkout (else cloned)")
    ap.add_argument("--only", help=f"comma-separated subset of {', '.join(DATASETS)}")
    args = ap.parse_args(argv)
    wanted = args.only.split(",") if args.only else list(DATASETS)
    unknown = set(wanted) - set(DATASETS)
    if unknown:
        ap.error(f"unknown dataset(s): {', '.join(sorted(unknown))}")
    try:
        cache = data_dir()
        sources = []
        if "creddata" in wanted:
            if args.creddata:
                sources.append(setup.creddata_source(args.creddata.resolve()))
            else:
                print("creddata: skipped, no --creddata path (clone Samsung/CredData and run its download_data.py)")
        if "tab" in wanted:
            sources.append(setup.tab_source(args.tab.resolve() if args.tab else None, cache))
        if "gretel" in wanted:
            sources.append(setup.gretel_source(cache))
        setup.run(sources, setup.default_out(), log=print)
    except BenchError as exc:
        print(f"setup: {exc}", file=sys.stderr)
        return 1
    print(f"data in {setup.default_out()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
