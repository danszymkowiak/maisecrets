"""The text of a document, changed: spans cut at cell edges, rule hits masked for the models, and the redacted
output as text or as CSV (TASK-34, TASK-49, TASK-54, TASK-59)."""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from .document import Document, Span


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


def render_tables(doc: Document, spans: Iterable[Span],
                  placeholder: Callable[[Span, str], str]) -> list[list[list[str]]]:
    """Each table of the document as rows of redacted cells (TASK-54). A span lies in one cell (within_cells); the
    placeholders are taken in text order, as render takes them. A span outside every cell is not written."""
    ordered = sorted(spans, key=lambda s: (s.start, -s.end))
    starts = [s.start for s in ordered]
    out = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = []
            for a, b in row:
                parts, at = [], a
                for s in ordered[bisect.bisect_left(starts, a):bisect.bisect_left(starts, b)]:
                    if s.start < at or s.end > b:
                        continue
                    parts += [doc.text[at:s.start], placeholder(s, doc.text[s.start:s.end])]
                    at = s.end
                parts.append(doc.text[at:b])
                cells.append("".join(parts))
            rows.append(cells)
        out.append(rows)
    return out


def to_csv(rows: Iterable[list[str]], delimiter: str) -> str:
    """Rows as CSV (RFC 4180): a cell with the delimiter, a quote, a tab or a line break is quoted."""
    special = re.compile("[" + re.escape(delimiter) + '"\t\n\r]')

    def cell(v: str) -> str:
        return '"' + v.replace('"', '""') + '"' if special.search(v) else v
    return "".join(delimiter.join(cell(v) for v in row) + "\r\n" for row in rows)


def safe_names(names: list[str]) -> list[str]:
    """A file-name part for each sheet: characters other than letters, digits, space, dot, dash and underscore become
    _, edge dots and spaces go; an empty name becomes sheet<n>, and a name taken twice gets -2, -3."""
    out: list[str] = []
    for n, name in enumerate(names, 1):
        safe = re.sub(r"[^\w .-]", "_", name).strip(" .") or f"sheet{n}"
        base, k = safe, 2
        while safe in out:
            safe, k = f"{base}-{k}", k + 1
        out.append(safe)
    return out


def overlapping(spans: Iterable[Span]) -> Callable[[int, int], bool]:
    """A test whether a stretch [start, end) overlaps any of the spans, in log time (TASK-59: the vote checked every
    model span against every rule span)."""
    merged: list[list[int]] = []
    for s in sorted(spans, key=lambda s: s.start):
        if s.start >= s.end:
            continue
        if merged and s.start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], s.end)
        else:
            merged.append([s.start, s.end])
    starts = [m[0] for m in merged]

    def test(start: int, end: int) -> bool:
        i = bisect.bisect_left(starts, end) - 1      # the last merged stretch that starts before end
        return i >= 0 and merged[i][1] > start
    return test


def within_cells(doc: Document, spans: Iterable[Span]) -> list[Span]:
    """Each span cut at the edges of the document's positions (a table's cells, a PDF's pages), so one placeholder
    never covers two cells (TASK-49); a part between two positions that holds only blanks is dropped."""
    edges = sorted({e for p in doc.positions for e in (p.start, p.end)})
    out = []
    for s in spans:
        i, j = bisect.bisect_right(edges, s.start), bisect.bisect_left(edges, s.end)      # TASK-59
        if i >= j:                          # inside one position: kept whole, as before
            if doc.text[s.start:s.end].strip():
                out.append(s)
            continue
        cuts = [s.start] + edges[i:j] + [s.end]
        for a, b in zip(cuts, cuts[1:]):
            if doc.text[a:b].strip():
                out.append(Span(a, b, s.type, s.source, s.score))
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
        out, starts = [], [seg[0] for seg in self.segments]
        for s in spans:
            i = max(bisect.bisect_right(starts, s.start) - 1, 0)      # segments are sorted and touch (TASK-59)
            for k in range(i, len(self.segments)):
                ms, me, os_, placeholder = self.segments[k]
                if ms >= s.end:
                    break
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
