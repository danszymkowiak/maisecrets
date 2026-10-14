"""What a file comes out as (TASK-54): a table as CSV (one per sheet of a workbook), every other document as text."""
from __future__ import annotations

from pathlib import PurePath

from .document import Document, Span
from .text import render, render_tables, safe_names, to_csv


TEXT_SUFFIX, TABLE_SUFFIX = ".redacted.txt", ".redacted.csv"


OUTPUT_SUFFIXES = (TEXT_SUFFIX, TABLE_SUFFIX)


TABLES = (".csv", ".tsv", ".xlsx", ".xlsm")


def output_name(path: PurePath) -> str:
    """The output of a file (TASK-54): a table comes out as CSV, every other document as text. For a workbook it is
    the base of one <file>.<sheet>.redacted.csv per sheet."""
    return path.name + (TABLE_SUFFIX if path.suffix.lower() in TABLES else TEXT_SUFFIX)


def outputs(doc: Document, target: PurePath, redact: list[Span],
             placeholder) -> list[tuple[PurePath, str]]:
    """(path, content) of each output: one CSV per table (per sheet for a workbook), else the text."""
    if not doc.tables:
        return [(target, render(doc, redact, placeholder))]
    tables = render_tables(doc, redact, placeholder)
    if len(doc.tables) == 1 and doc.tables[0].name is None:
        return [(target, to_csv(tables[0], doc.tables[0].delimiter))]
    base = target.name.removesuffix(TABLE_SUFFIX)
    hidden = [t.name_at is not None and any(s.start < t.name_at[1] and t.name_at[0] < s.end for s in redact)
              for t in doc.tables]
    names = safe_names(["" if h else (t.name or "") for t, h in zip(doc.tables, hidden)])
    return [(target.with_name(f"{base}.{n}{TABLE_SUFFIX}"), to_csv(rows, t.delimiter))
            for n, t, rows in zip(names, doc.tables, tables)]
