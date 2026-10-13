#!/usr/bin/env python3
"""What the decode stage costs on the bench's own texts (TASK-11.26, docs/BENCHMARK.md, Decode and rescan):

    uv run --project bench python bench/decodecost.py [--only creddata,gretel] [--limit 20000]

Per text: the bytes the stage decoded and the time of normalise(text, ("decode",)) alone (the rescan of a changed
text is the second pass every stage pays; bench/normtime.py measures it). Prints p50, p99 and the worst case per
dataset. Run it on an idle machine.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time

from maisecrets_bench import detector  # noqa: F401  first: the plugin on the path, with a temp home
from maisecrets_bench import schema
from maisecrets_bench.paths import data_dir

from maisecrets import decode, normalise  # noqa: E402


def _q(xs: list[float], q: float) -> float:
    return statistics.quantiles(xs, n=100)[q - 1] if len(xs) > 1 else (xs[0] if xs else 0.0)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="creddata,gretel,synthetic,findocs,nemotron,tab")
    ap.add_argument("--limit", type=int, default=20_000, help="texts per dataset")
    args = ap.parse_args(argv)
    print("| dataset | texts | changed | decoded bytes p50 / p99 / max | ms p50 / p99 / max |\n|---|---|---|---|---|")
    for name in args.only.split(","):
        rows = schema.read(data_dir() / "parquet" / f"{name}.parquet")[:args.limit]
        sizes, times, changed = [], [], 0
        for s in rows:
            b = decode.Budget()
            decode.decode_text(s.text, decode.MAX_DEPTH, b)
            sizes.append(decode.MAX_DECODED - b.decoded)
            t0 = time.perf_counter()
            n = normalise.normalise(s.text, ("decode",))
            times.append((time.perf_counter() - t0) * 1000)
            changed += n.text is not s.text
        print(f"| {name} | {len(rows)} | {changed} | {_q(sizes, 50):.0f} / {_q(sizes, 99):.0f} / {max(sizes)} "
              f"| {_q(times, 50):.2f} / {_q(times, 99):.2f} / {max(times):.1f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
