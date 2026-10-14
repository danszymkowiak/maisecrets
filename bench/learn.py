#!/usr/bin/env python3
"""Train the learned filter of the generic keyword rules on the dev split (TASK-11.27 b;
maisecrets_bench/adapters/plugin/learned.py):

    uv run --project bench python bench/learn.py [--run <data>/runs/<time>]

Reads the hits of learned.RULES in a full run (default: the newest), labels each by the scorer (tp or fp; neutral,
unjudged and unreviewed hits are left out), trains on dev only and writes maisecrets_bench/domain/learned_table.py: the
coefficients and the threshold that keeps every dev find. Prints counts and the weights, never a value.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maisecrets_bench.adapters import parquet_store
from maisecrets_bench.adapters.plugin import learned
from maisecrets_bench.domain import run_report
from maisecrets_bench.domain import score
from maisecrets_bench.adapters.locations import data_dir

OUT = Path(__file__).resolve().parent / "maisecrets_bench" / "domain" / "learned_table.py"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--epochs", type=int, default=300)
    args = ap.parse_args(argv)
    runs = sorted((data_dir() / "runs").glob("*/detections.parquet"))
    src = args.run or runs[-1].parent
    import json
    names = json.loads((src / "datasets.json").read_text(encoding="utf-8"))["datasets"]
    det = parquet_store.load_detections(src / "detections.parquet")
    xs, ys = [], []
    for n in names:
        for s in parquet_store.read(data_dir() / "parquet" / f"{n}.parquet"):
            if s.split != "dev":
                continue
            for d in det.get((s.dataset, s.sample_id), []):
                if d.rule.split("#", 1)[0] not in learned.RULES:
                    continue
                kind = score.classify(s, d, run_report.UNLABELLED_NEGATIVE.get(s.dataset, True),
                                      run_report.JUDGED.get(s.dataset))
                if kind not in ("tp", "fp"):
                    continue
                xs.append(learned.features(s.text[d.start:d.end], s.text, d.start, d.end, d.rule.split("#", 1)[0]))
                ys.append(int(kind == "tp"))
    print(f"dev hits: {sum(ys)} finds, {len(ys) - sum(ys)} false positives")
    model = learned.train(xs, ys, epochs=args.epochs)
    t = learned.keep_all_threshold(model, [x for x, y in zip(xs, ys) if y])
    dropped = sum(learned.prob(model, x) < t for x, y in zip(xs, ys) if not y)
    print(f"threshold {t:.6f}: drops {dropped} dev false positives, keeps every dev find")
    for name, w in sorted(zip(learned.NAMES, model[0]), key=lambda p: -abs(p[1])):
        print(f"  {name:<28} {w:+.3f}")
    OUT.write_text(f'"""Written by bench/learn.py from run {src.name} (dev split only): coefficients and the\n'
                   f'threshold of the learned filter (TASK-11.27). Numbers only."""\n'
                   + learned.to_table(model, t, learned.NAMES), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
