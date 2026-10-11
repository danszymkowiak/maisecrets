"""Where the benchmark keeps its data (docs/BENCHMARK.md, Layout). The datasets, the parquet files and the run results
live outside the repository: a file there could be committed, and the tree scan would read it."""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class BenchError(Exception):
    """A setup or run problem the person must fix; the message names it, never a value."""


def data_dir() -> Path:
    """$MAISECRETS_BENCH_DATA, else ~/.cache/maisecrets-bench. A directory inside the repository is refused."""
    raw = os.environ.get("MAISECRETS_BENCH_DATA")
    d = Path(raw).expanduser().resolve() if raw else (Path.home() / ".cache" / "maisecrets-bench").resolve()
    if d == REPO or REPO in d.parents:
        raise BenchError(f"the data directory {d} is inside the repository; set MAISECRETS_BENCH_DATA to a "
                         "directory outside it")
    return d
