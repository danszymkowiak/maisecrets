#!/usr/bin/env python3
"""Fetch and normalise the benchmark datasets (docs/BENCHMARK.md). Run from the repository root:

    uv run --project bench python bench/setup.py --creddata ../CredData [--tab ../text-anonymization-benchmark]
    uv run --project bench python bench/setup.py --only gretel,tab

Without --creddata, CredData is skipped (its download takes hours; the message says how). TAB was dropped
(docs/BENCHMARK.md) and is built only with --only tab. ai4privacy is opt-in (--with-ai4privacy): academic and
non-commercial use only, for your own local measurement. kagglepii is opt-in too (--with-kaggle-pii): your own
Kaggle account, the competition rules accepted on kaggle.com, KAGGLE_API_TOKEN in the environment or .env. The data
goes to $MAISECRETS_BENCH_DATA (default ~/.cache/maisecrets-bench).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.domain.bench_error import BenchError
from maisecrets_bench.adapters.locations import data_dir

DATASETS = ("creddata", "gretel", "synthetic", "nemotron", "mendeley", "findocs", "tab", "ai4privacy", "kagglepii")
# TAB was dropped (saturated, out of scope); ai4privacy and kagglepii are opt-in (licence); synthetic and findocs are
# generated, nothing fetched
DEFAULT = ("creddata", "gretel", "synthetic", "nemotron", "mendeley", "findocs")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--creddata", type=Path, help="a CredData checkout after its download_data.py")
    ap.add_argument("--tab", type=Path, help="a text-anonymization-benchmark checkout (else cloned)")
    ap.add_argument("--only", help=f"comma-separated datasets of {', '.join(DATASETS)} (default: {', '.join(DEFAULT)})")
    ap.add_argument("--with-ai4privacy", action="store_true",
                    help="also ai4privacy: academic and non-commercial use only; for your own local measurement")
    ap.add_argument("--with-kaggle-pii", action="store_true",
                    help="also The Learning Agency Lab's PII competition: your Kaggle account, its rules accepted")
    args = ap.parse_args(argv)
    wanted = args.only.split(",") if args.only else list(DEFAULT)
    if args.with_ai4privacy and "ai4privacy" not in wanted:
        wanted.append("ai4privacy")
    if args.with_kaggle_pii and "kagglepii" not in wanted:
        wanted.append("kagglepii")
    unknown = set(wanted) - set(DATASETS)
    if unknown:
        ap.error(f"unknown dataset(s): {', '.join(sorted(unknown))}")
    try:
        cache = data_dir()
        sources = []
        if "creddata" in wanted:
            if args.creddata:
                sources.append(sources.creddata_source(args.creddata.resolve()))
            else:
                print("creddata: skipped, no --creddata path (clone Samsung/CredData and run its download_data.py)")
        if "tab" in wanted:
            sources.append(sources.tab_source(args.tab.resolve() if args.tab else None, cache))
        if "gretel" in wanted:
            sources.append(sources.gretel_source(cache))
        if "synthetic" in wanted:
            sources.append(sources.synthetic_source())
        if "nemotron" in wanted:
            sources.append(sources.nemotron_source(cache))
        if "mendeley" in wanted:
            sources.append(sources.mendeley_source(cache))
        if "findocs" in wanted:
            sources.append(sources.findocs_source())
        if "ai4privacy" in wanted:
            from maisecrets_bench.adapters.datasets.ai4privacy import LICENCE_NOTE
            print(LICENCE_NOTE)
            sources.append(sources.ai4privacy_source(cache))
        if "kagglepii" in wanted:
            from maisecrets_bench.adapters.datasets.kagglepii import LICENCE_NOTE as KAGGLE_NOTE
            print(KAGGLE_NOTE)
            sources.append(sources.kagglepii_source(cache))
        compose.setup_run(sources, sources.default_out(), log=print)
    except BenchError as exc:
        print(f"setup: {exc}", file=sys.stderr)
        return 1
    print(f"data in {sources.default_out()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
