"""Samsung CredData (docs/BENCHMARK.md, CredData). One sample per file; a file above `max_bytes` becomes windows of
`context` lines around its labelled lines, merged where they overlap. Each meta row is one gold span: its value
(ValueStart/ValueEnd on a single line), or its lines when it names no value. T is pos, F neg, X uncertain. Values
are never printed: a message names the repository, the file and the line."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterator

from ...domain.labels import LabelTable
from ...domain.bench_error import BenchError
from ...domain.samples import Sample, Span
from ...domain.split import split_of

DATASET = "creddata"
MAX_BYTES = 1 << 20      # a larger file is cut into windows
CONTEXT = 50             # lines kept on each side of a labelled line in a window
_GOLD = {"T": "pos", "X": "uncertain", "F": "neg"}


def _rows(root: Path) -> list[dict]:
    meta = sorted((root / "meta").glob("*.csv"))
    if not meta:
        raise BenchError(f"{root}: no meta/*.csv; is this a CredData checkout after download_data.py?")
    out = []
    for f in meta:
        with open(f, encoding="utf-8", newline="") as fh:
            out.extend(csv.DictReader(fh))
    return out


def count_rows(root: Path) -> dict:
    """Labelled rows per GroundTruth, straight from the meta files: what the spans must account for."""
    return dict(Counter(r["GroundTruth"] for r in _rows(root)))


def _int(v: str) -> int | None:
    return int(v) if v not in ("", "-1") else None


def _windows(numbers: list[int], n_lines: int, context: int) -> list[tuple[int, int]]:
    """Merged [first, last] line ranges (1-based, inclusive) around the labelled lines."""
    out: list[list[int]] = []
    for n in sorted(numbers):
        lo, hi = max(1, n - context), min(n_lines, n + context)
        if out and lo <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [(a, b) for a, b in out]


def _span(row: dict, lines: list[str], offsets: list[int], first: int, table: LabelTable, where: str) -> Span:
    """The gold span of one meta row in a text whose first line is file line `first`."""
    gt = row["GroundTruth"]
    if gt not in _GOLD:
        raise BenchError(f"{DATASET}: {where} line {row['LineStart']}: GroundTruth {gt!r} is not T, F or X")
    a, b = int(row["LineStart"]) - first, int(row["LineEnd"]) - first      # 0-based within the text
    if not 0 <= a <= b < len(lines):
        raise BenchError(f"{DATASET}: {where} lines {row['LineStart']}-{row['LineEnd']} are outside the file")
    vs, ve = _int(row["ValueStart"]), _int(row["ValueEnd"])
    if a == b and vs is not None and ve is not None and 0 <= vs < ve <= len(lines[a]):
        start, end = offsets[a] + vs, offsets[a] + ve
    else:
        start, end = offsets[a], offsets[b] + len(lines[b])
        if end == start:          # an empty line: its line break marks it
            end = start + 1
    return Span(start, end, row["Category"], table.type_of(row["Category"]), _GOLD[gt])


def _sample(rel: str, sid: str, repo: str, lines: list[str], first: int, rows: list[dict],
            table: LabelTable) -> Sample:
    offsets, pos = [], 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    text = "\n".join(lines)
    spans = sorted((_span(r, lines, offsets, first, table, rel) for r in rows), key=lambda s: (s.start, s.end))
    spans = [Span(s.start, min(s.end, len(text)), s.label, s.maisecrets_type, s.gold) for s in spans]
    return Sample(DATASET, sid, repo, "und", text, spans, split_of(DATASET, repo))


def samples(root: Path, table: LabelTable, max_bytes: int = MAX_BYTES, context: int = CONTEXT) -> Iterator[Sample]:
    root = Path(root)
    by_file: dict[str, list[dict]] = {}
    for r in _rows(root):
        by_file.setdefault(r["FilePath"], []).append(r)
    for rel in sorted(by_file):
        rows = by_file[rel]
        repo = rows[0]["RepoName"]
        path = root / rel
        if not path.is_file():
            raise BenchError(f"{DATASET}: {rel} is missing; run CredData's download_data.py first")
        lines = path.read_bytes().decode("utf-8", errors="replace").split("\n")
        if path.stat().st_size <= max_bytes:
            yield _sample(rel, rel, repo, lines, 1, rows, table)
            continue
        labelled = sorted({n for r in rows for n in range(int(r["LineStart"]), int(r["LineEnd"]) + 1)})
        for first, last in _windows(labelled, len(lines), context):
            inside = [r for r in rows if first <= int(r["LineStart"]) and int(r["LineEnd"]) <= last]
            yield _sample(rel, f"{rel}#{first}-{last}", repo, lines[first - 1:last], first, inside, table)
