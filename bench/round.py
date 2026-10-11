#!/usr/bin/env python3
"""An agent round (docs/BENCHMARK.md, Dev and check):

    uv run --project bench python bench/round.py brief [--run <dir>]              # what an agent may read
    uv run --project bench python bench/round.py judge <mutation.toml>... [--guard tab]

`brief` writes <data>/rounds/<time>/brief.md from the dev split of a full run. `judge` scores proposals on dev and
on check; its verdict (accepted, accepted within tolerance, rejected) is the worse of the two, and of check only the
verdict and the mean change show.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from maisecrets_bench import mutate, mutation, round as rnd, run, setup
from maisecrets_bench.paths import BenchError, data_dir


def _newest_full_run() -> Path:
    manifest = json.loads((setup.default_out() / "manifest.json").read_text(encoding="utf-8"))
    return run.newest_full_run(data_dir() / "runs", manifest)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief")
    b.add_argument("--run", type=Path)
    j = sub.add_parser("judge")
    j.add_argument("mutations", nargs="+", type=Path)
    j.add_argument("--run", type=Path)
    j.add_argument("--guard", default="")
    j.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    j.add_argument("--recall-tolerance", type=float, default=100 * mutation.RECALL_TOLERANCE,
                   help="recall points a dataset may lose when its score does not fall (default %(default).1f)")
    args = ap.parse_args(argv)
    out = data_dir() / "rounds" / time.strftime("%Y%m%d-%H%M%S")
    try:
        rdir = args.run or _newest_full_run()
        if args.cmd == "brief":
            out.mkdir(parents=True, exist_ok=True)
            (out / "brief.md").write_text(rnd.brief(rdir, setup.default_out()), encoding="utf-8")
            print(f"brief: {out / 'brief.md'} (from {rdir.name})")
            return 0
        in_run = json.loads((rdir / "datasets.json").read_text(encoding="utf-8"))["datasets"]
        roles = {**run.default_roles(in_run), **{n: "guard" for n in args.guard.split(",") if n}}
        results = rnd.judge([mutation.load(p) for p in args.mutations], rdir, setup.default_out(), roles, args.jobs,
                            args.recall_tolerance / 100)
    except BenchError as exc:
        print(f"round: {exc}", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    names = results[0]["dev"]["datasets"] if results else []
    lines = ["# Round verdicts", "", *run.licence_notes(names), "", f"Baseline `{rdir.name}`.", "",
             "| proposal | verdict | dev mean change | check mean change | dev per dataset |", "|---|---|---|---|---|"]
    for r in results:
        per = ", ".join(f"{n} {100 * d['score_delta']:+.2f}" for n, d in r["dev"]["datasets"].items())
        lines.append(f"| {r['name']} | {mutate.VERDICT_TEXT[r['verdict']]} | "
                     f"{100 * r['dev']['overall_delta']:+.2f} | {100 * r['check']['overall_delta']:+.2f} | {per} |")
    for r in results:
        if r["dev"]["reasons"]:
            lines.append(f"\n{r['name']}: dev worse: " + "; ".join(r["dev"]["reasons"]))
        if r["dev"]["beyond"]:
            lines.append(f"\n{r['name']}: dev beyond the tolerance: " + "; ".join(r["dev"]["beyond"]))
        if r["check"]["verdict"] != r["dev"]["verdict"]:
            lines.append(f"\n{r['name']}: check says {mutate.VERDICT_TEXT[r['check']['verdict']]}")
    (out / "verdicts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
