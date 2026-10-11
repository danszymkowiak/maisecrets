"""The label table of a dataset (bench/labels/<dataset>.toml): the dataset's own label -> a maisecrets type or
OUT_OF_SCOPE. A label not in the table stops the setup; every new label is a decision (docs/BENCHMARK.md)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .paths import REPO, BenchError

TABLES = REPO / "bench" / "labels"


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


def load(dataset: str, path: Path | None = None) -> LabelTable:
    from .detector import known_types
    from .schema import OUT_OF_SCOPE
    path = path or TABLES / f"{dataset}.toml"
    mapping = tomllib.loads(path.read_text(encoding="utf-8")).get("labels", {})
    for label, t in mapping.items():
        if t != OUT_OF_SCOPE and t not in known_types():
            raise BenchError(f"{dataset}: label {label!r} maps to {t!r}, which is not a maisecrets type")
    return LabelTable(dataset, dict(mapping))
