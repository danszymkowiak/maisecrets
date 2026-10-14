"""The label table of a dataset (bench/labels/<dataset>.toml): the dataset's own label -> a maisecrets type or
OUT_OF_SCOPE. A label not in the table stops the setup; every new label is a decision (docs/BENCHMARK.md)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .bench_error import BenchError


@dataclass(frozen=True)
class LabelTable:
    dataset: str
    mapping: dict

    def type_of(self, label: str) -> str:
        try:
            return self.mapping[label]
        except KeyError:
            raise BenchError(f"{self.dataset}: label {label!r} is not in the table "
                             f"(bench/labels/{self.dataset}.toml); map it to a type or OUT_OF_SCOPE") from None


def parse(dataset: str, data: dict, unknown_type: Callable[[str], bool]) -> LabelTable:
    """The table from the parsed TOML file ([labels]); a type the detector does not know stops."""
    from .samples import OUT_OF_SCOPE
    mapping = data.get("labels", {})
    for label, t in mapping.items():
        if t != OUT_OF_SCOPE and unknown_type(t):
            raise BenchError(f"{dataset}: label {label!r} maps to {t!r}, which is not a maisecrets type")
    return LabelTable(dataset, dict(mapping))
