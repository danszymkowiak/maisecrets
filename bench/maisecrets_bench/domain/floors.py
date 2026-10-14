"""The floor table (bench/floors.toml, docs/BENCHMARK.md, TASK-21): each scoring type has a tier with a recall floor
(a number, "no_regression" or "none"); a type no tier lists gets default_tier. Datasets have weights in the
false-positive objective (unlisted: 1). SECRET is one detector type over hundreds of labels, so for scoring it splits
into SECRET_PREFIXED (a token with a vendor's fixed shape) and SECRET_GENERIC (keyword passwords, generic keys): a
CredData category is prefixed when one of its colon-separated parts is in prefixed_parts, a label of another dataset
when "dataset:label" is in prefixed_labels."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from .bench_error import BenchError


SECRET_TYPES = ("SECRET_PREFIXED", "SECRET_GENERIC")


NAMED_FLOORS = ("no_regression", "none")


@dataclass(frozen=True)
class Floors:
    tiers: dict            # type -> (tier, floor)
    default: tuple         # (tier, floor) of an unlisted type
    weights: dict
    prefixed_parts: frozenset
    prefixed_labels: frozenset

    def tier_of(self, t: str) -> tuple:
        return self.tiers.get(t, self.default)

    def weight(self, dataset: str) -> float:
        return float(self.weights.get(dataset, 1.0))

    def scoring_type(self, dataset: str, label: str, t: str) -> str:
        """The type a gold span is scored as: SECRET split in two, every other type as it is."""
        if t != "SECRET":
            return t
        if dataset == "creddata" and set(label.split(":")) & self.prefixed_parts:
            return "SECRET_PREFIXED"
        if f"{dataset}:{label}" in self.prefixed_labels:
            return "SECRET_PREFIXED"
        return "SECRET_GENERIC"


def parse(data: dict, unknown_type: Callable[[str], bool], name: str = "floors.toml") -> Floors:
    """The table from the parsed TOML file; `name` is the file's name in the error messages."""
    tiers: dict[str, tuple] = {}
    by_name: dict[str, tuple] = {}
    for name, tier in data.get("tiers", {}).items():
        floor = tier.get("floor")
        if not (isinstance(floor, (int, float)) and 0 < floor <= 1) and floor not in NAMED_FLOORS:
            raise BenchError(f"{name}: tier {name!r} has floor {floor!r}: a share in (0, 1] or one of "
                             f"{', '.join(NAMED_FLOORS)}")
        by_name[name] = (name, floor)
        for t in tier.get("types", []):
            if t == "SECRET":
                raise BenchError(f"{name}: tier {name!r} lists SECRET; use {' or '.join(SECRET_TYPES)}")
            if t not in SECRET_TYPES and unknown_type(t):     # SECRET itself is refused above
                raise BenchError(f"{name}: tier {name!r} lists {t!r}, which is not a maisecrets type")
            if t in tiers:
                raise BenchError(f"{name}: {t!r} is in tiers {tiers[t][0]!r} and {name!r}")
            tiers[t] = (name, floor)
    default = data.get("default_tier", "default")
    if default not in by_name:
        raise BenchError(f"{name}: default_tier {default!r} is not a tier")
    secret = data.get("secret", {})
    return Floors(tiers, by_name[default], dict(data.get("weights", {})), frozenset(secret.get("prefixed_parts", [])),
                  frozenset(secret.get("prefixed_labels", [])))
