"""Mendeley Data "Synthetic Dataset for PII Detection and Anonymization in Financial Documents" (doi
10.17632/tzrjx692jy.1, CC BY 4.0; TASK-11.35): auditor reports, tax filings, compliance notices and transaction
confirmations in English. Two spreadsheets (Training_Set.xlsx, 45,000 rows; Testing_Set.xlsx, 30): the columns
Name, Credit Card, Email, URL, Phone, Address, Company, SSN hold the injected values, Text the document, and True
Predictions a Python literal of (start, end, label), read with ast.literal_eval, never run.

The texts carry mojibake: UTF-8 read as cp1252 (a right quote became three characters), after the offsets were
taken, so about 8% of the spans pointed a few characters early. repair() undoes it run by run, and every span lands
on its column's value again. The xlsx is read with the standard library (zipfile and ElementTree)."""
from __future__ import annotations

import ast
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from ...domain.labels import LabelTable
from ...domain.bench_error import BenchError
from ...domain.samples import Sample, Span
from ...domain.split import split_of

DATASET = "mendeley"
API = "https://data.mendeley.com/public-api/datasets/tzrjx692jy/files?folder_id=root&version=1"
FILES = ("Training_Set.xlsx", "Testing_Set.xlsx")
REVISION = "email-oos"      # part of the version: a change of the adapter or its table builds the parquet again
LABELS = {"name", "credit_card", "email", "url", "phone", "address", "company", "ssn"}
COLUMNS = ["Name", "Credit Card", "Email", "URL", "Phone", "Address", "Company", "SSN", "Text", "True Predictions"]
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _cp1252(lo: int, hi: int) -> str:
    return "".join(bytes([b]).decode("cp1252", errors="ignore") for b in range(lo, hi + 1))


# a UTF-8 sequence read as cp1252: a lead byte (0xC2-0xF4) and one to three continuation bytes (0x80-0xBF)
_MOJIBAKE_RE = re.compile(f"[{re.escape(_cp1252(0xC2, 0xF4))}][{re.escape(_cp1252(0x80, 0xBF))}]{{1,3}}")


def repair(text: str) -> str:
    def fix(m: re.Match) -> str:
        try:
            return m.group(0).encode("cp1252").decode("utf-8")
        except UnicodeError:
            return m.group(0)
    return _MOJIBAKE_RE.sub(fix, text)


@dataclass
class Stats:
    dropped: int = 0


def _predictions(sid: str, raw: str) -> list:
    try:
        got = ast.literal_eval(raw or "[]")
    except (ValueError, SyntaxError):
        raise BenchError(f"{DATASET}: {sid}: True Predictions is not a literal list") from None
    if not isinstance(got, list):
        raise BenchError(f"{DATASET}: {sid}: True Predictions is not a list")
    return got


def samples(rows: Iterable[dict], table: LabelTable, stats: Stats) -> Iterator[Sample]:
    """rows: the column letters of a sheet row (I: Text, J: True Predictions), with _file and _row."""
    for r in rows:
        sid = f"{r['_file']}:{r['_row']}"
        text = repair(r.get("I") or "")
        spans = []
        for start, end, label in _predictions(sid, r.get("J")):
            t = table.type_of(label)
            if not 0 <= start < end <= len(text):
                stats.dropped += 1
                continue
            spans.append(Span(start, end, label, t, "pos"))
        spans.sort(key=lambda s: (s.start, s.end))
        yield Sample(DATASET, sid, sid, "en", text, spans, split_of(DATASET, sid))


def read_xlsx(path: Path) -> Iterator[dict]:
    """The rows of the first sheet after its header, by column letter; the header must be COLUMNS."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{_NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{_NS}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    for n, row in enumerate(sheet.iter(f"{_NS}row")):
        out = {}
        for c in row.iter(f"{_NS}c"):
            col = re.match(r"[A-Z]+", c.get("r", "")).group(0)
            v = c.find(f"{_NS}v")
            if c.get("t") == "s" and v is not None:
                out[col] = shared[int(v.text)]
            elif c.get("t") == "inlineStr":
                out[col] = "".join(t.text or "" for t in c.iter(f"{_NS}t"))
            else:
                out[col] = v.text if v is not None else None
        if n == 0:
            got = [out.get(chr(65 + i)) for i in range(len(COLUMNS))]
            if got != COLUMNS:
                raise BenchError(f"{DATASET}: {path.name}: columns {got} are not {COLUMNS}")
            continue
        yield {**out, "_file": path.stem, "_row": int(row.get("r", n + 1))}


def _get(url: str, timeout: int) -> bytes:
    """A GET with a named client: Mendeley answers urllib's default User-Agent with 403."""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "maisecrets-bench (+https://github.com/Mcpgate-de/maisecrets)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise BenchError(f"{DATASET}: {url}: {exc}") from None


def files() -> list[dict]:
    """The dataset's files from Mendeley's public API: name, sha256 and download URL."""
    import json
    listing = json.loads(_get(API, 60))
    out = [{"name": f["filename"], "sha256": f["content_details"]["sha256_hash"],
            "url": f["content_details"]["download_url"]} for f in listing if f["filename"] in FILES]
    if sorted(f["name"] for f in out) != sorted(FILES):
        raise BenchError(f"{DATASET}: the API lists {[f['filename'] for f in listing]}, not {list(FILES)}")
    return out


def download(listing: list[dict], into: Path) -> list[Path]:
    """Each file once into `into`, checked against its sha256; a mismatch stops."""
    import hashlib
    into.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in listing:
        p = into / f["name"]
        if not (p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == f["sha256"]):
            p.write_bytes(_get(f["url"], 300))
        if hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            raise BenchError(f"{DATASET}: {f['name']} does not match its sha256 from the API")
        paths.append(p)
    return paths
