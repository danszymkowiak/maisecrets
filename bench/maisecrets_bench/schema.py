"""The one schema of every dataset (docs/BENCHMARK.md, One schema), checked before it is written to parquet. Error
messages name the sample and the offending field, never the text."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .paths import BenchError

OUT_OF_SCOPE = "OUT_OF_SCOPE"
GOLD = ("pos", "neg", "uncertain")
SPLITS = ("dev", "check")


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    label: str              # the dataset's own label
    maisecrets_type: str    # a detector type, or OUT_OF_SCOPE
    gold: str               # pos, neg or uncertain


@dataclass(frozen=True)
class Line:                 # CredData: the gold of one line of a file (1-based)
    line: int
    gold: str
    maisecrets_type: str


@dataclass
class Sample:
    dataset: str
    sample_id: str
    group_id: str
    language: str
    text: str
    spans: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    split: str = "dev"


ARROW = pa.schema([
    ("dataset", pa.string()), ("sample_id", pa.string()), ("group_id", pa.string()), ("language", pa.string()),
    ("text", pa.large_string()),
    ("spans", pa.list_(pa.struct([("start", pa.int32()), ("end", pa.int32()), ("label", pa.string()),
                                  ("maisecrets_type", pa.string()), ("gold", pa.string())]))),
    ("lines", pa.list_(pa.struct([("line", pa.int32()), ("gold", pa.string()), ("maisecrets_type", pa.string())]))),
    ("split", pa.string()),
])


def _check_type(s: Sample, t: str) -> None:
    from .detector import known_types
    if t != OUT_OF_SCOPE and t not in known_types():
        raise BenchError(f"{s.dataset}/{s.sample_id}: type {t!r} is not a maisecrets type")


def _check_gold(s: Sample, g: str) -> None:
    if g not in GOLD:
        raise BenchError(f"{s.dataset}/{s.sample_id}: gold {g!r} is not one of {', '.join(GOLD)}")


def validate(s: Sample) -> None:
    if s.split not in SPLITS:
        raise BenchError(f"{s.dataset}/{s.sample_id}: split {s.split!r} is not dev or check")
    for sp in s.spans:
        if not 0 <= sp.start < sp.end <= len(s.text):
            raise BenchError(f"{s.dataset}/{s.sample_id}: span {sp.start}-{sp.end} is outside the text "
                             f"(length {len(s.text)}) or empty")
        _check_gold(s, sp.gold)
        _check_type(s, sp.maisecrets_type)
    for ln in s.lines:
        if ln.line < 1:
            raise BenchError(f"{s.dataset}/{s.sample_id}: line {ln.line} is below 1")
        _check_gold(s, ln.gold)
        _check_type(s, ln.maisecrets_type)


def write(samples: list[Sample], path: Path) -> None:
    for s in samples:
        validate(s)
    rows = [{**asdict(s)} for s in samples]
    pq.write_table(pa.Table.from_pylist(rows, schema=ARROW), path)


def read(path: Path) -> list[Sample]:
    out = []
    for r in pq.read_table(path, schema=ARROW).to_pylist():
        r["spans"] = [Span(**x) for x in r["spans"]]
        r["lines"] = [Line(**x) for x in r["lines"]]
        out.append(Sample(**r))
    return out
