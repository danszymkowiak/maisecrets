#!/usr/bin/env python3
"""Export the false positives and misses of a run for review (docs/BENCHMARK.md, Error export):

    uv run --project bench python bench/errors.py [--run <dir>] [--split dev|check|all]

Writes errors.jsonl and errors.md into the run: rule, type, shape and the lowercase words before each error, never a
value. The default is the dev split: an agent reads dev errors only, and check is scored in totals.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.adapters import parquet_store
from maisecrets_bench.adapters import sources
from maisecrets_bench.domain import errors
from maisecrets_bench.domain import run_report
from maisecrets_bench.domain.bench_error import BenchError
from maisecrets_bench.adapters.locations import data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, help="a run directory (default: the newest)")
    ap.add_argument("--split", choices=("dev", "check", "all"), default="dev")
    args = ap.parse_args(argv)
    try:
        manifest = json.loads((sources.default_out() / "manifest.json").read_text(encoding="utf-8"))
        rdir = args.run or compose.newest_full_run(data_dir() / "runs", manifest)
        meta = json.loads((rdir / "datasets.json").read_text(encoding="utf-8"))
        det = parquet_store.load_detections(rdir / "detections.parquet")
        recs = []
        for name in meta["datasets"]:
            for s in parquet_store.read(sources.default_out() / f"{name}.parquet"):
                if args.split != "all" and s.split != args.split:
                    continue
                recs += errors.collect(s, det.get((s.dataset, s.sample_id), []),
                                       run_report.UNLABELLED_NEGATIVE.get(s.dataset, True),
                                       run_report.JUDGED.get(s.dataset))
    except BenchError as exc:
        print(f"errors: {exc}", file=sys.stderr)
        return 1
    recs = errors.mask_rare(recs)
    with open(rdir / f"errors-{args.split}.jsonl", "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    (rdir / f"errors-{args.split}.md").write_text(errors.summary(recs), encoding="utf-8")
    print(f"{sum(r['kind'] == 'fp' for r in recs)} false positives, {sum(r['kind'] == 'fn' for r in recs)} misses "
          f"({args.split}); {rdir / f'errors-{args.split}.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
