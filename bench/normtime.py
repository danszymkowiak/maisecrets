#!/usr/bin/env python3
"""The time the normaliser stages add to a hook's scan (TASK-11.25, docs/BENCHMARK.md, Normaliser):

    uv run --project bench python bench/normtime.py [--stages entity,ansi,...] [--repeat 15]

Synthetic input of 25 KB and 120 KB (the sizes of a large prompt and a large tool output): plain (no stage changes
it, the cost of looking), with a cat -n gutter on every line, and with ANSI colour on every line (a terminal capture;
in both a stage changes the text and the second pass runs). Prints the median time of detect.scan without stages and
with them. Run it on an idle machine: a busy one inflates both columns.
"""
from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path

# scan reads the terms file: a temp home, never the real one
os.environ["MAISECRETS_HOME"] = tempfile.mkdtemp(prefix="normtime-home-")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from maisecrets import detect  # noqa: E402

WORDS = ("the build step reads config from the environment and writes a report for each module before deploy "
         "server request response timeout retry user account invoice total payment status").split()
STAGES = ("ansi", "cr", "invisible", "gutter", "entity", "fullwidth")


def text(size: int, kind: str, seed: int = 25) -> str:
    r = random.Random(seed)
    lines, n = [], 0
    while n < size:
        line = " ".join(r.choice(WORDS) for _ in range(r.randint(6, 14)))
        if kind == "gutter":
            line = f"{len(lines) + 1:>6}\t{line}"
        if kind == "ANSI":
            line = f"\x1b[3{r.randint(1, 7)}m{line}\x1b[0m"
        lines.append(line)
        n += len(line) + 1
    return "\n".join(lines)[:size]


def median_ms(t: str, ruleset, repeat: int) -> float:
    detect.scan(t, ruleset=ruleset)          # warm: compiled patterns, imports
    times = []
    for _ in range(repeat):
        a = time.perf_counter()
        detect.scan(t, ruleset=ruleset)
        times.append((time.perf_counter() - a) * 1000)
    return statistics.median(times)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", default=",".join(STAGES))
    ap.add_argument("--repeat", type=int, default=15)
    args = ap.parse_args(argv)
    stages = tuple(s for s in args.stages.split(",") if s)
    off = detect.build(detect.Settings())
    on = detect.build(detect.Settings(normalise=stages))
    print(f"stages: {', '.join(stages)}; median of {args.repeat} scans")
    print("| input | without | with | added |\n|---|---|---|---|")
    for size in (25_000, 120_000):
        for kind in ("plain", "gutter", "ANSI"):
            t = text(size, kind)
            a, b = median_ms(t, off, args.repeat), median_ms(t, on, args.repeat)
            print(f"| {size // 1000} KB {kind} | {a:.0f} ms | {b:.0f} ms | {b - a:+.0f} ms |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
