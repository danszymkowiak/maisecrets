"""The bench's own files in the repository (label tables, the floor table, the gold exceptions, mutations, a word
list) and the file system for the use cases (the Files port)."""
from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path
from typing import Callable

from ..domain import exceptions, floors, labels, mutation
from ..domain.loo import _toml
from ..domain.mutation import Mutation
from ..domain.wordlike import MIN_WORD, words_of
from .locations import REPO

LABEL_TABLES = REPO / "bench" / "labels"
FLOORS = REPO / "bench" / "floors.toml"
EXCEPTIONS = REPO / "bench" / "gold_exceptions.json"


def load_labels(dataset: str, unknown_type: Callable[[str], bool], path: Path | None = None) -> labels.LabelTable:
    path = path or LABEL_TABLES / f"{dataset}.toml"
    return labels.parse(dataset, tomllib.loads(path.read_text(encoding="utf-8")), unknown_type)


def load_floors(unknown_type: Callable[[str], bool], path: Path | None = None) -> floors.Floors:
    path = path or FLOORS
    return floors.parse(tomllib.loads(path.read_text(encoding="utf-8")), unknown_type, path.name)


def load_exceptions(path: Path | None = None) -> list[dict]:
    path = path or EXCEPTIONS
    return exceptions.check(json.loads(path.read_text(encoding="utf-8")), path.name)


def load_mutation(path: Path) -> Mutation:
    return mutation.parse(tomllib.loads(Path(path).read_text(encoding="utf-8")), path)


def load_words(path: Path, min_len: int = MIN_WORD) -> frozenset:
    """The words of a word list file (domain/wordlike.py, words_of)."""
    return words_of(path.read_text(encoding="utf-8", errors="replace"), min_len)


def write_mutations(muts: list[Mutation], folder: Path) -> list[Path]:
    """Leave-one-out mutations as TOML files (TASK-18), into the data directory, never the repository."""
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for m in muts:
        rule = next(iter(m.disabled))
        p = folder / f"leave-out-{re.sub(r'[^a-z0-9]+', '-', rule.lower()).strip('-')}.toml"
        p.write_text(_toml(m), encoding="utf-8")
        paths.append(p)
    return paths


class LocalFiles:
    """The Files port on the local file system."""

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        return path.exists()

    def glob(self, folder: Path, pattern: str) -> list[Path]:
        return list(folder.glob(pattern))

    def replace(self, src: Path, dst: Path) -> None:
        os.replace(src, dst)
