"""A document and its spans (TASK-34): the text extracted from a file, a map from its offsets back to the source, its
tables, and the spans the detectors find in it."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass(frozen=True)
class Position:
    """Where a stretch of the text came from: a page of a PDF, a sheet and cell of a workbook, a row and column."""
    start: int
    end: int
    where: str


@dataclass(frozen=True)
class Table:
    """A table of the document (TASK-54): each cell's (start, end) in the text, row by row, so the redacted cells can
    be written back as CSV. `name` is the sheet of a workbook, None for a CSV; `name_at` where the name is in the text
    (a redacted name must not reach a file name)."""
    name: str | None
    delimiter: str
    rows: tuple[tuple[tuple[int, int], ...], ...]
    name_at: tuple[int, int] | None = None


@dataclass(frozen=True)
class Document:
    path: str
    text: str
    positions: tuple[Position, ...] = ()
    tables: tuple[Table, ...] = ()


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    type: str
    source: str            # the detector: "rules" or a model name
    score: float = 1.0


@dataclass(frozen=True)
class Decision:
    redact: tuple[Span, ...]
    review: tuple[Span, ...] = field(default=())


Detector = Callable[[Document], list[Span]]


DETECTORS: dict[str, Detector] = {}      # name -> detector; TASK-34.3 adds the rules, TASK-34.4 the models


def available_detectors() -> list[str]:
    return sorted(DETECTORS)


def detect(doc: Document, detectors: Iterable[Detector]) -> list[Span]:
    return sorted((s for d in detectors for s in d(doc)), key=lambda s: (s.start, -s.end))


class Unsupported(ValueError):
    """A file type the tool does not extract."""


class NoText(ValueError):
    """A document with no extractable text (a scanned PDF: OCR is out of scope; a PDF locked by a password)."""
