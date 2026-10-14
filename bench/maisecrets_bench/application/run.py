"""A bench run (docs/BENCHMARK.md, Metrics): the samples of the datasets, the detector over them in language groups,
the scores, the floors and the report. The samples, the detector and the files come in through the ports; results
hold counts and rule ids, never a value."""
from __future__ import annotations

import json
import random
import time
from collections import Counter
from pathlib import Path

from ..domain import floorscore, run_report
from ..domain.bench_error import BenchError
from ..domain.samples import Sample
from .ports import BenchPorts


def run(ports: BenchPorts, parquet: Path, datasets: list[str], out: Path, jobs: int, limit: int | None = None) -> dict:
    samples: list[Sample] = []
    for name in datasets:
        rows = ports.samples.read(parquet / f"{name}.parquet")
        if limit and len(rows) > limit:
            rows = random.Random(f"bench-limit-{name}").sample(rows, limit)
        samples += rows
    t0 = time.time()
    det, groups = ports.detector.detect(samples, jobs)
    summary = run_report.summarise(run_report.score_all(samples, det), groups, run_report.score_tags(samples, det))
    fs = floorscore.summarise(samples, det, ports.floors(), run_report.default_roles(datasets),
                              run_report.UNLABELLED_NEGATIVE, run_report.JUDGED)
    summary["floors"] = {k: v for k, v in fs.items() if k != "critical_misses"}
    summary["floors"]["critical_miss_counts"] = dict(Counter(m["type"] for m in fs["critical_misses"]))
    seconds = time.time() - t0
    manifest = json.loads(ports.files.read_text(parquet / "manifest.json"))
    ports.detections.save(det, out / "detections.parquet")
    ports.files.write_text(out / "critical_misses.tsv", run_report.critical_misses_tsv(fs))
    ports.files.write_text(out / "datasets.json", json.dumps({"datasets": datasets, "limit": limit}) + "\n")
    ports.files.write_text(out / "metrics.json", json.dumps({**summary, "seconds": seconds, "limit": limit,
                                                             "manifest": manifest}, indent=2) + "\n")
    ports.files.write_text(out / "report.md", run_report.report(summary, manifest, seconds))
    return summary


def newest_full_run(ports: BenchPorts, runs_dir: Path, manifest: dict) -> Path:
    """The newest run over every dataset of the manifest without --limit: what a baseline must be."""
    want = set(run_report.default_datasets(manifest))
    for p in sorted(ports.files.glob(runs_dir, "*/datasets.json"), reverse=True):
        meta = json.loads(ports.files.read_text(p))
        done = ports.files.exists(p.parent / "detections.parquet")
        if not meta.get("limit") and set(meta["datasets"]) == want and done:
            return p.parent
    raise BenchError(f"no run over all of {', '.join(sorted(want))} without --limit; run bench/run.py first")
