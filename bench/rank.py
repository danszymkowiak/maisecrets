#!/usr/bin/env python3
"""Rank a leave-one-out run (TASK-18.2; maisecrets_bench/rank.py says how):

    uv run --project bench python bench/rank.py [<data>/loo/<time>]

Writes rank.md next to the run's results.json (default: the newest leave-one-out run) and prints it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.domain import rank
from maisecrets_bench.adapters.locations import data_dir


def main(argv: list[str]) -> int:
    runs = sorted((data_dir() / "loo").glob("*/results.json"))
    src = Path(argv[0]) if argv else (runs[-1].parent if runs else None)
    if src is None or not (src / "results.json").is_file():
        print("rank: no leave-one-out run with a results.json", file=sys.stderr)
        return 1
    data = json.loads((src / "results.json").read_text(encoding="utf-8"))
    text = rank.report(rank.rows(data["results"], compose.load_floors().weights), Path(data["baseline"]).name)
    (src / "rank.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
