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


@dataclass
class Sample:
    dataset: str
    sample_id: str
    group_id: str
    language: str
    text: str
    spans: list = field(default_factory=list)
    split: str = "dev"
    tags: list = field(default_factory=list)     # facets the report scores apart: format:structured, locale:us


ARROW = pa.schema([
    ("dataset", pa.string()), ("sample_id", pa.string()), ("group_id", pa.string()), ("language", pa.string()),
    ("text", pa.large_string()),
    ("spans", pa.list_(pa.struct([("start", pa.int32()), ("end", pa.int32()), ("label", pa.string()),
                                  ("maisecrets_type", pa.string()), ("gold", pa.string())]))),
    ("split", pa.string()),
    ("tags", pa.list_(pa.string())),
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


def write(samples: list[Sample], path: Path) -> None:
    for s in samples:
        validate(s)
    rows = [{**asdict(s)} for s in samples]
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
