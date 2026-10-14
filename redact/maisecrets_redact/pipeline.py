"""The pipeline in pure functions (TASK-34): extract a document to text with a map back to its source, find spans with
the detectors, decide which to redact and which a person reviews, and render the redacted text. Each step is its own
function, testable on its own; the CLI only reads files, calls these and writes the result."""
from __future__ import annotations

import bisect
import re
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


def within_cells(doc: Document, spans: Iterable[Span]) -> list[Span]:
    """Each span cut at the edges of the document's positions (a table's cells, a PDF's pages), so one placeholder
    never covers two cells (TASK-49); a part between two positions that holds only blanks is dropped."""
    edges = sorted({e for p in doc.positions for e in (p.start, p.end)})
    out = []
    for s in spans:
        cuts = [s.start] + [e for e in edges if s.start < e < s.end] + [s.end]
        for a, b in zip(cuts, cuts[1:]):
            if doc.text[a:b].strip():
                out.append(Span(a, b, s.type, s.source, s.score))
    return out


_CELL = re.compile(r"(?:^|, )row (\d+), column (.*)$")
_SECRET_HEADERS = ("password", "passwd", "pwd", "passphrase", "secret", "token", "apikey", "privatekey")
_USERNAME_HEADERS = {"username", "user", "login", "loginname", "userid"}
_TIME_HEADERS = ("time", "date", "timestamp", "created", "modified", "updated", "changed", "lastused")
_GUID = re.compile(r"\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?")
_EPOCH = re.compile(r"\d{10}|\d{13}")       # seconds or milliseconds since 1970


def _norm(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.lower())


def header_type(header: str) -> str | None:
    """The type of every cell under a header that names it (TASK-50): SECRET for password, client_secret, api-key...,
    USERNAME for username, login...; None for any other header."""
    h = _norm(header)
    if h.endswith(_SECRET_HEADERS):
        return "SECRET"
    return "USERNAME" if h in _USERNAME_HEADERS else None


def _time_header(header: str) -> bool:
    h = _norm(header)
    return h.startswith("time") or h.endswith(_TIME_HEADERS) or re.search(r"(_at|[a-z]At)$", header) is not None


def cell(doc: Document, offset: int, starts: list[int] | None = None) -> tuple[int, str, Position] | None:
    """(row, header, position) of the table cell holding the offset; None outside a table. `starts`: the positions'
    starts, when the caller looks up many offsets."""
    starts = starts if starts is not None else [p.start for p in doc.positions]
    i = bisect.bisect_right(starts, offset) - 1
    if i < 0 or not doc.positions[i].start <= offset < doc.positions[i].end:
        return None
    m = _CELL.search(doc.positions[i].where)
    return (int(m.group(1)), m.group(2), doc.positions[i]) if m else None


def column_spans(doc: Document) -> list[Span]:
    """Each cell below a header that names its type (header_type): a deterministic hit, as a rule's is. A password
    export had its passwords in the clear: a bare value matches no rule and the models are not asked for passwords."""
    out = []
    for p in doc.positions:
        m = _CELL.search(p.where)
        typ = header_type(m.group(2)) if m and int(m.group(1)) > 1 else None
        if typ and doc.text[p.start:p.end].strip():
            out.append(Span(p.start, p.end, typ, "columns"))
    return out


def _token(doc: Document, s: Span, starts: list[int]) -> tuple[str, str | None]:
    """The whole value a span lies in, and its column header: the cell in a table, else the run of non-blanks."""
    c = cell(doc, s.start, starts)
    if c:
        return doc.text[c[2].start:c[2].end].strip(), c[1]
    a, b = s.start, s.end
    while a > 0 and not doc.text[a - 1].isspace():
        a -= 1
    while b < len(doc.text) and not doc.text[b].isspace():
        b += 1
    return doc.text[a:b].strip("\"'()[],;."), None


def plausible(doc: Document, spans: Iterable[Span]) -> list[Span]:
    """A model's span without the shape of its type is dropped: an EMAIL without an @ (gliner2 labels the city cell
    after an [EMAIL] placeholder 'email', TASK-49), and any span on a GUID or a piece of one, or on a 10- or 13-digit
    timestamp under a time header (models took a password export's record ids and times for national ids and accounts,
    TASK-50)."""
    out, starts = [], [p.start for p in doc.positions]
    for s in spans:
        if s.type == "EMAIL" and "@" not in doc.text[s.start:s.end]:
            continue
        token, header = _token(doc, s, starts)
        if _GUID.fullmatch(token) or (header is not None and _time_header(header) and _EPOCH.fullmatch(token)):
            continue
        out.append(s)
    return out


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
