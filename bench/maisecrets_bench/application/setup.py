"""Build the benchmark data (docs/BENCHMARK.md): each source becomes <out>/<dataset>.parquet and an entry in
<out>/manifest.json with its version and counts. Gold of a checksummed type is checked on the way (validgold.py); a
source whose version and gold revision are already in the manifest, with its file present, is not built again. The
sources themselves are adapters (adapters/sources.py)."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from ..domain import exceptions, split, validgold
from ..domain.samples import Sample
from .ports import BenchPorts


@dataclass
class Source:
    name: str
    version: Callable[[], str]
    build: Callable[[], Iterator[Sample]]
    stats: Callable[[], dict]


def _manifest(ports: BenchPorts, out: Path) -> dict:
    p = out / "manifest.json"
    return json.loads(ports.files.read_text(p)) if ports.files.exists(p) else {"datasets": {}}


def run(ports: BenchPorts, sources: list[Source], out: Path, log: Callable[[str], None] = lambda s: None,
        exceptions_file: Path | None = None) -> dict:
    manifest = _manifest(ports, out)
    entries = ports.exceptions(exceptions_file)
    for src in sources:
        version = src.version()
        known = manifest["datasets"].get(src.name, {})
        target = out / f"{src.name}.parquet"
        reviewed = exceptions.digest(entries, src.name)
        if (known.get("version") == version and known.get("gold") == validgold.REVISION
                and known.get("exceptions") == reviewed and ports.files.exists(target)):
            log(f"{src.name}: up to date ({version})")
            continue
        log(f"{src.name}: building ({version})")
        rows, gold = validgold.mark(list(src.build()), ports.detector.gold_checks())
        rows, applied = exceptions.apply(rows, entries)
        tmp = target.with_suffix(".parquet.tmp")
        ports.samples.write(rows, tmp)
        ports.files.replace(tmp, target)
        spans = Counter(sp.gold for s in rows for sp in s.spans)
        manifest["datasets"][src.name] = {
            "version": version, "samples": len(rows), "spans": dict(sorted(spans.items())),
            "split": dict(sorted(Counter(s.split for s in rows).items())), **src.stats(),
            "gold": validgold.REVISION, "gold_check": gold.get(src.name, {}),
            "exceptions": reviewed, "exceptions_applied": applied}
        log(f"{src.name}: {len(rows)} samples, spans {dict(spans)}")
    manifest["split_salt"] = split.SALT
    ports.files.write_text(out / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
