"""The samples and the detections as parquet files (pyarrow): the bench's data on disk. Implements the SampleStore
and DetectionStore ports."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

import pyarrow as pa
import pyarrow.parquet as pq

from ..domain import score
from ..domain.bench_error import BenchError
from ..domain.samples import Sample, Span, validate


ARROW = pa.schema([
    ("dataset", pa.string()), ("sample_id", pa.string()), ("group_id", pa.string()), ("language", pa.string()),
    ("text", pa.large_string()),
    ("spans", pa.list_(pa.struct([("start", pa.int32()), ("end", pa.int32()), ("label", pa.string()),
                                  ("maisecrets_type", pa.string()), ("gold", pa.string())]))),
    ("split", pa.string()),
    ("tags", pa.list_(pa.string())),
])


def write(samples: list[Sample], path: Path, unknown_type: Callable[[str], bool]) -> None:
    seen = set()
    for s in samples:
        validate(s, unknown_type)
        key = (s.dataset, s.sample_id)
        if key in seen:
            raise BenchError(f"{s.dataset}/{s.sample_id}: sample id twice; detections are keyed by it")
        seen.add(key)
    rows = [{**asdict(s)} for s in samples]
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=ARROW), path)


def read(path: Path) -> list[Sample]:
    """The samples of a file; one written before tags existed reads with none."""
    names = pq.read_schema(path).names
    arrow = ARROW if "tags" in names else pa.schema([f for f in ARROW if f.name != "tags"])
    out = []
    for r in pq.read_table(path, schema=arrow).to_pylist():
        r["spans"] = [Span(**x) for x in r["spans"]]
        out.append(Sample(**r))
    return out


DETECTIONS = pa.schema([("dataset", pa.string()), ("sample_id", pa.string()), ("start", pa.int32()),
                        ("end", pa.int32()), ("type", pa.string()), ("rule", pa.string())])


def save_detections(det: dict, path: Path) -> None:
    """Positions, types and rule ids: what rescoring needs, and no value."""
    rows = [{"dataset": k[0], "sample_id": k[1], "start": d.start, "end": d.end, "type": d.type, "rule": d.rule}
            for k, ds in det.items() for d in ds]
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=DETECTIONS), path)


def load_detections(path: Path) -> dict:
    det: dict[tuple[str, str], list[score.Detection]] = {}
    for r in pq.read_table(path, schema=DETECTIONS).to_pylist():
        det.setdefault((r["dataset"], r["sample_id"]), []).append(score.Detection(r["start"], r["end"], r["type"],
                                                                                    r["rule"]))
    return det


class ParquetStore:
    """The SampleStore and DetectionStore ports. unknown_type checks the types of samples before a write."""

    def __init__(self, unknown_type: Callable[[str], bool]) -> None:
        self.unknown_type = unknown_type

    def read(self, path: Path) -> list[Sample]:
        return read(path)

    def write(self, samples: list[Sample], path: Path) -> None:
        write(samples, path, self.unknown_type)

    def save(self, det: dict, path: Path) -> None:
        save_detections(det, path)

    def load(self, path: Path) -> dict:
        return load_detections(path)
