"""The password shape (TASK-55): a password-like token in free text becomes a review item."""
from __future__ import annotations

import re

from .document import Document, Span
from .fields import _CARD_FIELD, _CELL, _words


# The password shape (TASK-55): a token of 8 to 64 characters with three of lower case, upper case, digits and
# symbols, that has no shape of an id, a number, a code, a word with digits or punctuation, or markup. Each exclusion
# below removed a group of false hits on the bench text (gretel, nemotron, findocs, tab, mendeley; docs/REDACT.md).
_NOT_PASSWORDS = [
    re.compile(r"\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?"),  # GUID
    re.compile(r"[0-9A-Fa-f]{16,}"),                                   # a hash, a hex id
    re.compile(r"[\d.:/T+Z-]+"),                                       # dates, times, numbers
    re.compile(r"v?\d+(?:\.\d+)+(?:[-+.][\w.]+)?"),                    # versions
    re.compile(r"#?[A-Z]{1,6}[-_]?\d+(?:[-_./]\d+)*"),                 # references: COVID-19, ISO-9001, #INV12345
    re.compile(r"(?:[A-Z]{3})?[\d.,'’]+[^\W\d_]{0,3}%?"),              # amounts: CHF1,200.50, 15.5kg
    re.compile(r"[^\W\d_]+\d{1,4}"),                                   # a word and digits: Version2024
    re.compile(r"[a-z][a-z0-9]*(?:[_\-][a-z0-9]+)+"),                  # snake_case, kebab-case identifiers
    re.compile(r"[0-9A-Fa-f]*(?:[:.-][0-9A-Fa-f]*){2,}"),              # IPv6, MAC addresses
    re.compile(r"[a-z0-9._-]+@[a-z][a-z0-9-]*"),                       # a mail handle: name12@host
    re.compile(r"[A-Z]{2,3}\+.*"),                                     # an EDIFACT segment
    re.compile(r"[^\W_]+\([^\W_]+\)[^\W_]*"),                          # Account(s)
    re.compile(r"\w+[=:]\S*"),                                         # key=value, TAG:42
    re.compile(r"#[^\W\d_]+"),                                         # a hashtag
    re.compile(r"[A-Z]+\d*\*.*"),                                       # an X12 segment: N1*...
    re.compile(r"⟦[^⟧]*⟧"),                                            # a maisecrets placeholder
]


_MARKUP = re.compile(r'="|<|>|&[a-z]+;|\*\*|^:\d{2}[A-Z]?:|"|\]\(|^!\[|\|')  # markup, SWIFT tag, JSON, Markdown


_MAIL = re.compile(r"[^@\s]+@[\w-]+(?:\.[\w-]+)+")


_REPEATED_SEP = re.compile(r"([*~+:|,;=]).*\1")                    # EDI segments, CSV pieces: A*9*9~, A,B,9.9


_SEGMENT = re.compile(r"\d+|[^\W\d_]+|[A-Z0-9]+")                   # one class, or upper case and digits


_LEAD, _TRAIL = "([{'\"‘“„«¡¿*:", ".,;:)]}'\"’”“»*-"


_PROSE = set("-'’,;:!?().‑_&…")                                    # the symbols of words and sentences


def _core(token: str) -> tuple[int, int]:
    """(start, end) of a token without the sentence punctuation around it."""
    a = len(token) - len(token.lstrip(_LEAD))
    return a, max(a, len(token.rstrip(_TRAIL)))


def password_shaped(token: str) -> bool:
    """Has the token the shape of a password (TASK-55)? See _NOT_PASSWORDS for what is left out."""
    if _MARKUP.search(token):
        return False
    a, b = _core(token)
    t = token[a:b]
    if not 8 <= len(t) <= 64 or _REPEATED_SEP.search(t) or _MAIL.fullmatch(t):
        return False
    if "://" in t or t.startswith("www.") or "/" in t or "\\" in t:
        return False
    parts = re.split(r"[-+_./]", t)
    if len(parts) > 1 and all(_SEGMENT.fullmatch(p) for p in parts if p):
        return False                       # a code or a phrase: 2024-Q1-05, AB-12-C, 5-star, Summer-2024
    symbols = {c for c in t if not c.isalnum()}
    digits = any(c.isdigit() for c in t)
    if not digits and symbols <= _PROSE:
        return False                       # words and punctuation: Jean-Pierre, l'Économie, Hello,World, Wow!
    classes = sum([any(c.islower() for c in t), any(c.isupper() for c in t), digits, bool(symbols)])
    return classes >= 3 and not any(p.fullmatch(t) for p in _NOT_PASSWORDS)


_FREE_TEXT_WORDS = {"note", "notes", "comment", "comments", "description", "extra", "memo", "remark", "remarks",
                    "details", "bemerkung", "bemerkungen", "notiz", "notizen", "kommentar"}


_TOKEN = re.compile(r"\S+")


def _free_text(where: str) -> bool:
    """Is a position free text: a whole text file or PDF page, a notes-like column below its header, or the NOTE,
    DESCRIPTION, COMMENT or SUMMARY of a vCard or iCalendar file."""
    if where == "file" or where.startswith("page "):
        return True
    m = _CELL.search(where)
    if m:
        w = _words(m.group(2))
        return int(m.group(1)) > 1 and bool(w) and w[-1] in _FREE_TEXT_WORDS
    m = _CARD_FIELD.search(where)
    return bool(m) and not m.group(2) and m.group(1) in {"NOTE", "DESCRIPTION", "COMMENT", "SUMMARY"}


def shape_spans(doc: Document) -> list[Span]:
    """Password-shaped tokens in free text (TASK-55): review items only, never a redaction of their own."""
    out = []
    for p in doc.positions:
        if not _free_text(p.where):
            continue
        for m in _TOKEN.finditer(doc.text, p.start, p.end):
            if password_shaped(m.group()):
                a, b = _core(m.group())
                out.append(Span(m.start() + a, m.start() + b, "SECRET", "password-shape"))
    return out
