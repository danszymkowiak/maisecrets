"""Where the benchmark keeps its data (docs/BENCHMARK.md, Layout). The datasets, the parquet files and the run results
live outside the repository: a file there could be committed, and the tree scan would read it. Every adapter may
import this module; it is outside the independence contract."""
from __future__ import annotations

import os
from pathlib import Path

from ..domain.bench_error import BenchError


def _checkout() -> Path:
    """The checkout this file is in: the nearest folder above it with bench/ and maisecrets/ (TASK-62: a fixed count
    of parent folders broke silently when a module moved)."""
    here = Path(__file__).resolve()
    return next((p for p in here.parents if (p / "bench").is_dir() and (p / "maisecrets").is_dir()), here.parents[3])


REPO = _checkout()


def data_dir() -> Path:
    """$MAISECRETS_BENCH_DATA, else ~/.cache/maisecrets-bench. A directory inside the repository is refused."""
    raw = os.environ.get("MAISECRETS_BENCH_DATA")
    d = Path(raw).expanduser().resolve() if raw else (Path.home() / ".cache" / "maisecrets-bench").resolve()
    if d == REPO or REPO in d.parents:
        raise BenchError(f"the data directory {d} is inside the repository; set MAISECRETS_BENCH_DATA to a "
                         "directory outside it")
    return d
