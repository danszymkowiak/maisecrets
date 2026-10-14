"""The ports of the application (TASK-62): what a run needs from the outside, as Protocols. The adapters implement
them; adapters/compose.py puts one of each into a Ports bundle."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..domain.document import Detector, Document
from ..domain.models import Backend as ModelBackend
from ..domain.review_items import Item

__all__ = ["Detector", "Extractor", "ModelBackend", "OutputSink", "Ports", "ReviewStore", "Tree"]


class Extractor(Protocol):
    def supports(self, path: Path) -> bool: ...

    def extract(self, path: Path, drop_columns: frozenset[str]) -> Document: ...


class ReviewStore(Protocol):
    """The decisions of a person on the open items of one output (`target`)."""

    def read(self, target: Path, doc: Document) -> dict[str, object]: ...   # empty when there is none

    def write(self, target: Path, doc: Document, items: list[Item], decided: dict[str, object]) -> None: ...


class OutputSink(Protocol):
    def exists(self, path: Path) -> bool: ...

    def write(self, path: Path, text: str) -> None: ...


class Tree(Protocol):
    """The files of a folder, in a fixed order (placeholders are numbered in it)."""

    def files(self, root: Path, recursive: bool) -> list[Path]: ...

    def inside(self, path: Path, root: Path) -> bool: ...          # after following links

    def same(self, a: Path, b: Path) -> bool: ...

    def is_link(self, path: Path) -> bool: ...


@dataclass(frozen=True)
class Ports:
    extractor: Extractor
    rules: Detector
    reviews: ReviewStore
    sink: OutputSink
    tree: Tree
