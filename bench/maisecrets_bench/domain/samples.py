"""The one schema of every dataset (docs/BENCHMARK.md, One schema), checked before it is written. Error messages name
the sample and the offending field, never the text. The parquet form is in adapters/parquet_store.py."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .bench_error import BenchError


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


def _check_type(s: Sample, t: str, unknown_type: Callable[[str], bool]) -> None:
    if t != OUT_OF_SCOPE and unknown_type(t):
        raise BenchError(f"{s.dataset}/{s.sample_id}: type {t!r} is not a maisecrets type")


def _check_gold(s: Sample, g: str) -> None:
    if g not in GOLD:
        raise BenchError(f"{s.dataset}/{s.sample_id}: gold {g!r} is not one of {', '.join(GOLD)}")


def validate(s: Sample, unknown_type: Callable[[str], bool]) -> None:
    """unknown_type: is a type name not one the detector reports (the plugin adapter's unknown_type)."""
    if s.split not in SPLITS:
        raise BenchError(f"{s.dataset}/{s.sample_id}: split {s.split!r} is not dev or check")
    for sp in s.spans:
        if not 0 <= sp.start < sp.end <= len(s.text):
            raise BenchError(f"{s.dataset}/{s.sample_id}: span {sp.start}-{sp.end} is outside the text "
                             f"(length {len(s.text)}) or empty")
        _check_gold(s, sp.gold)
        _check_type(s, sp.maisecrets_type, unknown_type)
