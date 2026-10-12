"""The pipeline in pure functions (TASK-34): extract a document to text with a map back to its source, find spans with
the detectors, decide which to redact and which a person reviews, and render the redacted text. Each step is its own
function, testable on its own; the CLI only reads files, calls these and writes the result."""
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
class Document:
    path: str
    text: str
    positions: tuple[Position, ...] = ()


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


def render(doc: Document, spans: Iterable[Span], placeholder: Callable[[Span, str], str]) -> str:
    """The text with each span replaced; overlapping spans merge into the first, which covers both."""
    out, at = [], 0
    for s in sorted(spans, key=lambda s: (s.start, -s.end)):
        if s.start < at:
            continue
        out += [doc.text[at:s.start], placeholder(s, doc.text[s.start:s.end])]
        at = s.end
    out.append(doc.text[at:])
    return "".join(out)


@dataclass(frozen=True)
class Masked:
    """The text the models read after the rules (user, 2026-10-12): each rule hit replaced by [TYPE]. segments maps
    it back: (masked start, masked end, original start, is a placeholder)."""
    doc: Document
    segments: tuple[tuple[int, int, int, bool], ...] = ()
    original: str = ""

    def back(self, spans: Iterable[Span]) -> list[Span]:
        """Model spans of the masked text in original offsets; the part of a span on a placeholder is dropped (the
        rules hold that value), and what is left on either side is kept when it holds more than blanks and
        punctuation."""
        if not self.segments:
            return list(spans)
        out = []
        for s in spans:
            for ms, me, os_, placeholder in self.segments:
                a, b = max(s.start, ms), min(s.end, me)
                if a >= b or placeholder:
                    continue
                a, b = a - ms + os_, b - ms + os_
                text = self.original[a:b]
                lead = len(text) - len(text.lstrip(" \t,;:"))
                trail = len(text) - len(text.rstrip(" \t,;:"))
                if b - trail > a + lead:
                    out.append(Span(a + lead, b - trail, s.type, s.source, s.score))
        return out


def mask(doc: Document, rule_spans: Iterable[Span]) -> Masked:
    rules = sorted(rule_spans, key=lambda s: (s.start, -s.end))
    if not rules:
        return Masked(doc)
    parts, segments, at, pos = [], [], 0, 0
    for s in rules:
        if s.start < at:
            continue
        if s.start > at:
            parts.append(doc.text[at:s.start])
            segments.append((pos, pos + s.start - at, at, False))
            pos += s.start - at
        ph = f"[{s.type}]"
        parts.append(ph)
        segments.append((pos, pos + len(ph), s.start, True))
        pos += len(ph)
        at = s.end
    if at < len(doc.text):
        parts.append(doc.text[at:])
        segments.append((pos, pos + len(doc.text) - at, at, False))
    return Masked(Document(doc.path, "".join(parts), doc.positions), tuple(segments), doc.text)
