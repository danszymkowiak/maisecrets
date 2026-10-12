#!/usr/bin/env python3
"""Audit the gold of every dataset against candidate validity rules (TASK-30, docs/BENCHMARK.md, Valid gold):

    uv run --project bench python bench/audit.py [--only gretel,nemotron]

Writes <data>/audit/<time>/report.md and results.json: per dataset and type, how many positives fail each candidate
rule, with example shapes, never a value. Nothing is changed; the rules chosen from it go into validgold.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from maisecrets_bench import audit, schema, setup
from maisecrets_bench.paths import BenchError, data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated datasets (default: all in the manifest)")
    args = ap.parse_args(argv)
    try:
        manifest = json.loads((setup.default_out() / "manifest.json").read_text(encoding="utf-8"))
        names = args.only.split(",") if args.only else sorted(manifest["datasets"])
        result = {}
        for name in names:
            path = setup.default_out() / f"{name}.parquet"
            if path.exists():
                result.update(audit.audit(schema.read(path)))
    except BenchError as exc:
        print(f"audit: {exc}", file=sys.stderr)
        return 1
    out = data_dir() / "audit" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "report.md").write_text(audit.report(result), encoding="utf-8")
    print(f"report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
