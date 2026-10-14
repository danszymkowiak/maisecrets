#!/usr/bin/env python3
"""Recall under perturbation (docs/BENCHMARK.md, Perturbation):

    uv run --project bench python bench/perturb.py [--only gretel,synthetic] [--per-dataset 400] [--mutation m.toml]

Writes <data>/perturb/<time>/report.md: recall per transform (zero-width, soft hyphen, fullwidth, homoglyph, ANSI
reset, CR, wrap, base64, hex, HTML entity, markdown escape, truncation) and dataset, against the untouched text.
With --mutation the detector runs mutated (a normaliser stage, TASK-11.25), and the report names the mutation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from maisecrets_bench.adapters import files
from maisecrets_bench.adapters import parquet_store
from maisecrets_bench.adapters.plugin import mutations
from maisecrets_bench.adapters.plugin import pool
from maisecrets_bench.adapters import sources
from maisecrets_bench.domain import perturb
from maisecrets_bench.domain import run_report
from maisecrets_bench.domain.bench_error import BenchError
from maisecrets_bench.adapters.locations import data_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated datasets (default: those of a default run)")
    ap.add_argument("--per-dataset", type=int, default=400, help="samples with a positive per dataset")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--mutation", type=Path, help="run the detector with this mutation applied")
    args = ap.parse_args(argv)
    try:
        mut = files.load_mutation(args.mutation) if args.mutation else None
        if mut:
            mutations.validate(mut)
        parquet = sources.default_out()
        manifest = json.loads((parquet / "manifest.json").read_text(encoding="utf-8"))
        names = args.only.split(",") if args.only else run_report.default_datasets(manifest)
        picked = {n: perturb.pick(parquet_store.read(parquet / f"{n}.parquet"), args.per_dataset) for n in names}
        table = {}
        for t, fn in perturb.TRANSFORMS.items():
            rows = [r for n in names for s in picked[n] if (r := perturb.rewrite(s, fn)) is not None]
            det, _ = pool.detect_samples(rows, args.jobs, mutation=mut)
            table[t] = perturb.recall(rows, det, run_report.UNLABELLED_NEGATIVE, run_report.JUDGED)
            print(f"{t:12} " + "  ".join(f"{n} {f}/{p}" for n, (f, p) in sorted(table[t].items())), flush=True)
    except BenchError as exc:
        print(f"perturb: {exc}", file=sys.stderr)
        return 1
    out = data_dir() / "perturb" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    head = f"Mutation: {mut.name} ({args.mutation.name}).\n\n" if mut else ""
    text = ("\n".join(run_report.licence_notes(names)) + "\n\n" + head
            + perturb.report(table, {n: len(v) for n, v in picked.items()}))
    (out / "report.md").write_text(text, encoding="utf-8")
    (out / "results.json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    print(text)
    print(f"report: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
