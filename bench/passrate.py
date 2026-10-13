#!/usr/bin/env python3
"""Checksum pass rates of a run's hits (TASK-11.24; maisecrets_bench/passrate.py says what is counted):

    uv run --project bench python bench/passrate.py [<data>/runs/<time>]

Writes passrate.md into the run (default: the newest full run) and prints it. The rules are the Presidio recognizers
that validate in Presidio but not in the plugin's port, each with its bench validator (validators.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

from maisecrets_bench import passrate, schema
from maisecrets_bench.paths import data_dir

CHECKS = {"es-nif": "bench:es_nif", "es-nie": "bench:es_nie", "it-vat-code": "bench:it_vat", "nhs": "bench:nhs",
          "us-npi": "bench:us_npi", "se-organisationsnummer": "bench:se_org",
          "uk-vehicle-registration": "bench:uk_vehicle", "aba-routing": "bench:aba",
          "se-personnummer": "bench:se_pnr"}


def main(argv: list[str]) -> int:
    runs = sorted((data_dir() / "runs").glob("*/detections.parquet"))
    src = Path(argv[0]) if argv else (runs[-1].parent if runs else None)
    if src is None or not (src / "detections.parquet").is_file():
        print("passrate: no run with a detections.parquet", file=sys.stderr)
        return 1
    names = json.loads((src / "datasets.json").read_text(encoding="utf-8"))["datasets"]
    samples = {(s.dataset, s.sample_id): s for n in names for s in schema.read(data_dir() / "parquet" / f"{n}.parquet")}
    dets = pq.read_table(src / "detections.parquet").to_pylist()
    text = passrate.report(passrate.table(samples, dets, CHECKS), src.name)
    (src / "passrate.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
