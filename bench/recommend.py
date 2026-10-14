#!/usr/bin/env python3
"""Write the recommendations page of a round (TASK-11.14, docs/BENCHMARK.md):

    uv run --project bench python bench/recommend.py --mutations <dir> [<dir> ...] [--baseline <run>]

Reads the baseline run's metrics.json and each mutation run's results.json and writes
<data>/recommendations/<time>/recommendations.md: counts, rule ids and reasons, never a value, and no local-only
dataset (ai4privacy). Sharing it upstream is the user's step.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.adapters import sources
from maisecrets_bench.domain import recommend
from maisecrets_bench.domain import run_report
from maisecrets_bench.domain.bench_error import BenchError
from maisecrets_bench.adapters.locations import data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=Path, help="a full run directory (default: the newest full run)")
    ap.add_argument("--mutations", type=Path, nargs="+", required=True, help="mutation run directories")
    args = ap.parse_args(argv)
    try:
        manifest = json.loads((sources.default_out() / "manifest.json").read_text(encoding="utf-8"))
        base_dir = args.baseline or compose.newest_full_run(data_dir() / "runs", manifest)
        baseline = json.loads((base_dir / "metrics.json").read_text(encoding="utf-8"))
        runs = [json.loads((d / "results.json").read_text(encoding="utf-8")) for d in args.mutations]
    except (BenchError, OSError, ValueError) as exc:
        print(f"recommend: {exc}", file=sys.stderr)
        return 1
    text = recommend.page(baseline, runs, local_only=set(run_report.LOCAL_ONLY), baseline_id=base_dir.name)
    out = data_dir() / "recommendations" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "recommendations.md").write_text(text, encoding="utf-8")
    print(f"report: {out / 'recommendations.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
