"""Extractors (TASK-34.2): a document becomes flattened text and a map from text offsets back to its source. One
function per format. A table also keeps where each of its cells lies in the text, so its redacted cells can be written
back as CSV (TASK-54); a PDF is never rebuilt (docs/REDACT.md).

- PDF: digital text with pypdf (BSD-3-Clause), page by page. No OCR: a PDF without text raises NoText.
- CSV: the csv module, cell by cell, the delimiter sniffed; a column can be dropped by its header.
- Excel: openpyxl (MIT), every sheet, cell values (not formulas), a column dropped by its header.
- HAR (TASK-52): every request and response of a browser session, one field per position (`entry 3, request header
  Cookie`), so the field names can say which values are secrets. Binary, script and style bodies are left out.
- vCard and iCalendar (TASK-53): folded lines unfolded, each property value a position (`card 2, field TEL`), and
  the CN, EMAIL and SENT-BY parameters too (`event 1, field ATTENDEE CN`). Photos, logos, sounds and keys are left out.
- .txt and .md pass through.
"""
from __future__ import annotations

import csv
import re
import io
import json
from pathlib import Path
from urllib.parse import unquote_plus

from .pipeline import Document, Position, Table


class Unsupported(ValueError):
    """A file type the tool does not extract."""


class NoText(ValueError):
    """A document with no extractable text (a scanned PDF: OCR is out of scope)."""


class _Builder:
    """Text and positions built together, so every offset maps back to where it came from."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.positions: list[Position] = []
        self.tables: list[Table] = []
        self.size = 0

    def add(self, text: str, where: str | None = None) -> None:
        if where is not None and text:
            self.positions.append(Position(self.size, self.size + len(text), where))
        self.parts.append(text)
        self.size += len(text)

    def document(self, path: Path) -> Document:
        return Document(str(path), "".join(self.parts), tuple(self.positions), tuple(self.tables))


def _drop(headers: list[str], drop: set[str]) -> set[int]:
    wanted = {d.strip().lower() for d in drop}
    return {i for i, h in enumerate(headers) if str(h or "").strip().lower() in wanted}


def _table(b: _Builder, rows: list[list[str]], drop: set[str], prefix: str = "", name: str | None = None,
           delimiter: str = ",", name_at: tuple[int, int] | None = None) -> None:
    """Rows as tab-separated lines; the first row names the columns. The table, without its dropped columns, is
    recorded too."""
    headers = [str(h) if h is not None else "" for h in rows[0]] if rows else []
    skip = _drop(headers, drop)
    table = []
    for r, row in enumerate(rows, 1):
        cells = [(c, v) for c, v in enumerate(row) if c not in skip]
        spans = []
        for n, (c, value) in enumerate(cells):
            header = headers[c] if c < len(headers) and headers[c] else _column_letter(c)
            start = b.size
            b.add("" if value is None else str(value), f"{prefix}row {r}, column {header}")
            spans.append((start, b.size))
            if n < len(cells) - 1:
                b.add("\t")
        b.add("\n")
        table.append(tuple(spans))
    b.tables.append(Table(name, delimiter, tuple(table), name_at))


def _column_letter(i: int) -> str:
    out = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        out = chr(65 + rem) + out
    return out


def _pdf(path: Path) -> Document:
    from pypdf import PdfReader
    b = _Builder()
    for n, page in enumerate(PdfReader(str(path)).pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            b.add(text, f"page {n}")
            b.add("\n\n")
    doc = b.document(path)
    if not doc.text.strip():
        raise NoText(f"{path.name}: no text found (a scanned PDF? OCR is out of scope)")
    return doc


def _csv(path: Path, drop: set[str]) -> Document:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel
    b = _Builder()
    # newline="": a quoted cell may hold a line break
    _table(b, list(csv.reader(io.StringIO(raw, newline=""), dialect)), drop, delimiter=dialect.delimiter)
    return b.document(path)


def _excel(path: Path, drop: set[str]) -> Document:
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    b = _Builder()
    try:
        for ws in wb.worksheets:
            at = b.size + 1
            b.add(f"[{ws.title}]\n")
            _table(b, [list(r) for r in ws.iter_rows(values_only=True)], drop, prefix=f"sheet {ws.title}, ",
                   name=ws.title, name_at=(at, at + len(ws.title)))
            b.add("\n")
    finally:
        wb.close()
    return b.document(path)


def _fields(b: _Builder, where: str, kind: str, items, sep: str) -> None:
    for item in items or ():
        name, value = str(item.get("name", "")), str(item.get("value", ""))
        b.add(f"{kind}{name}{sep}")
        b.add(value, f"{where} {kind.strip() or 'header'} {name}")
        b.add("\n")


_TEXT_BODY = ("json", "xml", "html", "text/plain", "x-www-form-urlencoded", "csv")


def _har_url(b: _Builder, where: str, url: str) -> None:
    """The URL as it is, each query value its own position (a token in a query string)."""
    base, q, query = url.partition("?")
    b.add(base + q, f"{where} url")
    for n, pair in enumerate(query.split("&") if query else []):
        if n:
            b.add("&")
        name, eq, value = pair.partition("=")
        b.add(name + eq)
        b.add(value, f"{where} query {unquote_plus(name)}")


def _har(path: Path) -> Document:
    try:
        entries = json.loads(path.read_text(encoding="utf-8-sig"))["log"]["entries"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"{path.name}: not a HAR file ({exc.__class__.__name__})") from None
    b = _Builder()
    for n, entry in enumerate(entries, 1):
        req, resp = entry.get("request") or {}, entry.get("response") or {}
        where = f"entry {n}, request"
        b.add(f"[entry {n}] {req.get('method', '')} ")
        _har_url(b, where, str(req.get("url", "")))
        b.add("\n")
        _fields(b, where, "", req.get("headers"), ": ")
        _fields(b, where, "cookie ", req.get("cookies"), "=")
        post = req.get("postData") or {}
        if post.get("params"):
            _fields(b, where, "form ", post["params"], "=")      # its raw text holds the same values: not written
        elif post.get("text"):
            b.add("body: ")
            b.add(str(post["text"]), f"{where} body")
            b.add("\n")
        where = f"entry {n}, response"
        b.add(f"response {resp.get('status', '')} {resp.get('statusText', '')}\n")
        _fields(b, where, "", resp.get("headers"), ": ")
        _fields(b, where, "cookie ", resp.get("cookies"), "=")
        content = resp.get("content") or {}
        mime = str(content.get("mimeType", "")).lower()
        if content.get("text") and content.get("encoding") != "base64" and any(t in mime for t in _TEXT_BODY):
            b.add("body: ")
            b.add(str(content["text"]), f"{where} body")
            b.add("\n")
        b.add("\n")
    return b.document(path)


_PERSON_PARAMS = {"CN", "EMAIL", "SENT-BY"}
_LEFT_OUT = {"PHOTO", "LOGO", "SOUND", "KEY", "ATTACH"}        # binary, or no personal text
_PARAM = re.compile(r';([A-Za-z0-9-]+)=("[^"]*"|[^;:]*)')
_CONTENT = re.compile(r'^((?:[A-Za-z0-9-]+\.)?([A-Za-z0-9-]+))((?:;[A-Za-z0-9-]+=(?:"[^"]*"|[^;:]*))*):(.*)$')


def _cards(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = re.sub(r"\r?\n[ \t]", "", raw).splitlines()       # unfold (RFC 6350 3.2, RFC 5545 3.1)
    b = _Builder()
    counts: dict[str, int] = {}
    where = "file"
    for line in lines:
        m = _CONTENT.match(line)
        if not m:
            b.add(line, where if line.strip() else None)
            b.add("\n")
            continue
        full, name, params, value = m.group(1), m.group(2).upper(), m.group(3), m.group(4)
        if name == "BEGIN" and value.upper() != "VCALENDAR":
            kind = "card" if value.upper() == "VCARD" else value.lower().removeprefix("v")
            counts[kind] = counts.get(kind, 0) + 1
            where = f"{kind} {counts[kind]}"
        if name in _LEFT_OUT:
            b.add(f"{full}: (left out)\n")
            continue
        b.add(full)
        at = 0
        for p in _PARAM.finditer(params):
            b.add(params[at:p.start(2)])
            b.add(p.group(2), f"{where}, field {name} {p.group(1).upper()}" if p.group(1).upper() in _PERSON_PARAMS
                  else None)
            at = p.end(2)
        b.add(params[at:] + ":")
        b.add(value, f"{where}, field {name}")
        b.add("\n")
    return b.document(path)


def _plain(path: Path) -> Document:
    b = _Builder()
    b.add(path.read_text(encoding="utf-8", errors="replace"), "file")
    return b.document(path)


SUPPORTED = (".pdf", ".csv", ".tsv", ".xlsx", ".xlsm", ".har", ".vcf", ".ics", ".txt", ".md")


def extract(path: Path | str, drop_columns: set[str] | frozenset[str] = frozenset()) -> Document:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix in (".csv", ".tsv"):
        return _csv(path, set(drop_columns))
    if suffix in (".xlsx", ".xlsm"):
        return _excel(path, set(drop_columns))
    if suffix == ".har":
        return _har(path)
    if suffix in (".vcf", ".ics"):
        return _cards(path)
    if suffix in (".txt", ".md"):
        return _plain(path)
    raise Unsupported(f"{path.name}: {suffix.lstrip('.') or 'no extension'} is not a supported type "
                      f"({', '.join(SUPPORTED)})")
