"""The pipeline in pure functions (TASK-34): extract a document to text with a map back to its source, find spans with
the detectors, decide which to redact and which a person reviews, and render the redacted text. Each step is its own
function, testable on its own; the CLI only reads files, calls these and writes the result."""
from __future__ import annotations

import bisect
import functools
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


_CELL = re.compile(r"(?:^|, )row (\d+), column (.*)$")
# Headers match by their words (camelCase, _ - . and spaces split them; TASK-56): the last word names what a cell holds,
# or the last two together (api_key, access_token, user_id). `token` alone is an NLP column, `is_secret` a flag.
_SECRET_WORDS = {"password", "passwd", "pwd", "passphrase", "secret", "totp", "hotp", "otp"}   # a 2FA seed too
_SECRET_PAIRS = {"apikey", "privatekey", "secretkey", "accesskey", "accesstoken", "apitoken", "authtoken",
                 "refreshtoken", "bearertoken", "sessiontoken", "idtoken", "otpauth"}
_USERNAME_WORDS = {"username", "user", "login", "loginname", "userid"}
_NOT_USERNAME_PAIRS = {"lastlogin", "firstlogin"}       # a time
_FLAG_WORDS = {"is", "has"}
# Personal types (TASK-51). `name`, `account`, `title` and `city` alone stay plain: a password manager names its entries
# so, and a product or a town is not a person.
_NAME_WORDS = {"surname", "forename", "vorname", "nachname", "firstname", "lastname", "fullname", "givenname",
               "familyname"}
_NAME_OWNERS = {"first", "last", "full", "given", "family", "middle", "maiden", "customer", "contact", "employee",
                "person", "patient"}
_DOB_WORDS = {"dob", "birthdate", "birthday", "geburtsdatum", "geburtstag"}
_NUMBER_WORDS = {"number", "num", "no", "nr"}           # stripped from the end: passport_number is passport
_IDS = {"NATIONAL_ID": {"ssn", "ahv", "socialsecurity", "nationalid", "nin", "personnummer"},
        "PASSPORT": {"passport"}, "TAX_ID": {"taxid", "tin", "steuernummer", "steuerid"},
        "ACCOUNT": {"iban", "bankaccount", "kontonummer"}}
_NUMBERED_ACCOUNT = {"account", "acct", "konto"}         # only with a number word: Account alone is an entry title
_PHONE_WORDS = {"phone", "telephone", "mobile", "tel", "fax", "telefon", "handy"}
_ADDRESS_WORDS = {"address", "addr", "street", "strasse", "adresse"}
_NOT_POSTAL = {"email", "mail", "ip", "mac", "web", "url", "wallet", "server", "host", "ipv4", "ipv6", "bitcoin"}
_TIME_WORDS = {"time", "date", "datetime", "timestamp", "ts", "epoch", "mtime", "ctime", "created", "modified",
               "updated", "changed", "at"}
_TIME_PAIRS = {"lastused", "lastseen"}
_GUID = re.compile(r"\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?")
_EPOCH = re.compile(r"\d{10}|\d{13}")       # seconds or milliseconds since 1970
_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")


def _words(header: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(header)]


@functools.lru_cache(maxsize=4096)      # once per column, not per cell (TASK-59)
def header_type(header: str) -> str | None:
    """The type of every cell under a header that names it (TASK-50): SECRET for password, client_secret, api-key, a
    TOTP seed..., USERNAME for username, login_username..., and the personal types for first_name, dob, ssn, iban,
    phone, address... (TASK-51); None for any other header, a flag such as isSecret among them."""
    w = _words(header)
    if not w or w[0] in _FLAG_WORDS:
        return None
    pair = "".join(w[-2:])
    if w[-1] in _SECRET_WORDS or pair in _SECRET_PAIRS:
        return "SECRET"
    if (w[-1] in _USERNAME_WORDS or pair in _USERNAME_WORDS) and pair not in _NOT_USERNAME_PAIRS:
        return "USERNAME"
    return _personal_type(w)


def _personal_type(w: list[str]) -> str | None:
    whole = "".join(w)
    if whole in _NAME_WORDS or (len(w) > 1 and w[-1] == "name" and w[-2] in _NAME_OWNERS):
        return "NAME"
    if whole in _DOB_WORDS or ("birth" in w and ("date" in w or "day" in w)):
        return "DOB"
    core = list(w)
    while len(core) > 1 and (core[-1] in _NUMBER_WORDS or core[-1].isdigit() or core[-1] == "line"):
        core.pop()
    joined = "".join(core)
    for typ, names in _IDS.items():
        if joined in names:
            return typ
    if joined in _NUMBERED_ACCOUNT and len(core) < len(w):
        return "ACCOUNT"
    if core[-1] in _PHONE_WORDS:
        return "PHONE"
    if core[-1] in _ADDRESS_WORDS and not _NOT_POSTAL & set(w):
        return "ADDRESS"
    return None


_HAR_FIELD = re.compile(r"(?:^|, )(request|response) (header|cookie|query|form) (.+)$")
_SECRET_HTTP_HEADERS = {"cookie", "set-cookie", "authorization", "proxy-authorization"}


def har_spans(doc: Document) -> list[Span]:
    """The fields of a HAR file that name a secret (TASK-52): every cookie, the Cookie, Set-Cookie and Authorization
    headers, a header whose name is a secret's (X-Api-Key), and a query or form value under a name header_type knows
    (access_token, password, user). Deterministic hits, as a table's columns are."""
    out = []
    for p in doc.positions:
        m = _HAR_FIELD.search(p.where)
        if not m:
            continue
        kind, name = m.group(2), m.group(3)
        if kind == "cookie" or (kind == "header" and name.lower() in _SECRET_HTTP_HEADERS):
            typ = "SECRET"
        elif kind == "header":
            typ = "SECRET" if header_type(name) == "SECRET" else None
        else:
            typ = header_type(name)
        if typ and doc.text[p.start:p.end].strip():
            out.append(Span(p.start, p.end, typ, "fields"))
    return out


_CARD_FIELD = re.compile(r"(?:^|, )field ([A-Z0-9-]+)(?: ([A-Z0-9-]+))?$")
_CARD_TYPES = {"FN": "NAME", "N": "NAME", "NICKNAME": "NAME", "CN": "NAME", "TEL": "PHONE", "EMAIL": "EMAIL",
               "SENT-BY": "EMAIL", "ORGANIZER": "EMAIL", "ATTENDEE": "EMAIL", "ADR": "ADDRESS", "LABEL": "ADDRESS",
               "LOCATION": "ADDRESS", "BDAY": "DOB", "IMPP": "USERNAME"}
_FREE_TEXT = {"NOTE", "SUMMARY", "DESCRIPTION", "COMMENT", "X-ALT-DESC"}
# a meeting's passcode: in a join link (?pwd=...) or after its label (Passcode: 482910); an escaped line break (\n,
# RFC 5545 3.3.11) may stand right before the label
_PASSCODE = re.compile(r"[?&](?:pwd|passcode|password|pin)=([^&\s\\]+)"
                       r"|(?:(?<=\\n)|\b)(?i:(?:passcode|password|passwort|kennwort|meeting pin|pin)\s*[:=]\s*)"
                       r"([^\s\\,;]+)")


def card_spans(doc: Document) -> list[Span]:
    """The labelled fields of a vCard or iCalendar file (TASK-53): FN and N a NAME, TEL a PHONE, ATTENDEE an EMAIL and
    its CN a NAME, LOCATION and ADR an ADDRESS, BDAY a DOB; in free text (NOTE, DESCRIPTION...) a meeting passcode is
    a SECRET, and the rest goes to the rules and models."""
    out = []
    for p in doc.positions:
        m = _CARD_FIELD.search(p.where)
        if not m:
            continue
        field, param = m.group(1), m.group(2)
        typ = _CARD_TYPES.get(param or field)
        value = doc.text[p.start:p.end]
        if typ and value.strip():
            out.append(Span(p.start, p.end, typ, "fields"))
        elif field in _FREE_TEXT and not param:
            for c in _PASSCODE.finditer(value):
                g = 1 if c.group(1) else 2
                out.append(Span(p.start + c.start(g), p.start + c.end(g), "SECRET", "fields"))
    return out


@functools.lru_cache(maxsize=4096)
def _time_header(header: str) -> bool:
    w = _words(header)
    return any(x in _TIME_WORDS for x in w) or any(a + b in _TIME_PAIRS for a, b in zip(w, w[1:]))


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


_ID_WORDS = {"id", "guid", "uuid"}
_ID_PIECE = re.compile(r"[0-9A-Fa-f{}-]+")      # a span on a GUID or a timestamp holds only these (TASK-59)
_GUID_LABELS = {"ACCOUNT", "NATIONAL_ID"}       # what the models call a record's GUID in a table (TASK-50)


def _id_header(header: str) -> bool:
    w = _words(header)
    return bool(w) and w[-1] in _ID_WORDS


def _guid_verdict(s: Span, token: str, header: str | None) -> str | None:
    """For a model span on a GUID or a piece of one (token: the whole value, _token; TASK-57): 'drop' under an id
    header, or labelled an account or a national id in a table cell; 'ask' anywhere else (a UUID-shaped API key or
    customer id); None off a GUID."""
    if not _GUID.fullmatch(token):
        return None
    if header is not None and (_id_header(header) or s.type in _GUID_LABELS):
        return "drop"
    return "ask"


def plausible(doc: Document, spans: Iterable[Span]) -> list[Span]:
    """A model's span without the shape of its type is dropped: an EMAIL without an @ (gliner2 labels the city cell
    after an [EMAIL] placeholder 'email', TASK-49), a span on a GUID where the column says it is an id (models took a
    password export's record ids for national ids and accounts, TASK-50, TASK-57), and one on a 10- or 13-digit
    timestamp under a time header."""
    out, starts = [], [p.start for p in doc.positions]
    for s in spans:
        if s.type == "EMAIL" and "@" not in doc.text[s.start:s.end]:
            continue
        if not _ID_PIECE.fullmatch(doc.text[s.start:s.end].strip()):
            out.append(s)
            continue
        token, header = _token(doc, s, starts)
        if _guid_verdict(s, token, header) == "drop" or (header is not None and _time_header(header)
                                                        and _EPOCH.fullmatch(token)):
            continue
        out.append(s)
    return out


def doubtful(doc: Document, spans: Iterable[Span]) -> list[Span]:
    """The model spans a person decides even when the models agree (TASK-57): a GUID outside an id column. Dropped,
    a UUID-shaped key would be written in the clear; redacted, every record id would go."""
    starts = [p.start for p in doc.positions]
    return [s for s in spans if _ID_PIECE.fullmatch(doc.text[s.start:s.end].strip())
            and _guid_verdict(s, *_token(doc, s, starts)) == "ask"]


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
