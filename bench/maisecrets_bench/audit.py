"""The gold audit (TASK-30): how much gold of each type fails a candidate validity rule, per dataset, before any rule
is applied to the gold. Types without a checksum (phone, e-mail, IP, US bank number) get candidates here; the
checksum types are judged by validgold.py already. A reason names why a value is no valid value; examples are shapes
(errors.shape: letters as a/A, digits as 9), never a value."""
from __future__ import annotations

import ipaddress
import re
from typing import Callable, Iterable

from .errors import shape
from .schema import Sample

_EXTENSION = re.compile(r"(?i)\s*(?:ext\.?|x|#)\s*\d{1,6}\s*$")
_US_LAYOUT = re.compile(r"\(?\d{3}\)?[-. ]?\d{3}[-. ]\d{4}")
_NANP_PREFIX = re.compile(r"\s*(?:\+\s?1|1(?=[-. (]))[-. ]?")


def _phone(v: str) -> list[str]:
    v = _EXTENSION.sub("", v.strip())
    out = []
    if re.search(r"[^\W\d_]", v):
        out.append("phone-letters")
    digits = re.sub(r"\D", "", v.replace("(0)", ""))
    if digits.startswith("00"):
        digits = digits[2:]
    if not 7 <= len(digits) <= 15:
        out.append("phone-digits")
    if digits and len(set(digits)) == 1:
        out.append("phone-repeated")
    national = None
    m = _NANP_PREFIX.match(v)
    if m and len(re.sub(r"\D", "", v[m.end():])) == 10:
        national = re.sub(r"\D", "", v[m.end():])
    elif _US_LAYOUT.fullmatch(v) and not re.sub(r"\D", "", v).startswith("0"):
        # a leading 0 is a trunk prefix outside North America (030-438-8690, (022) 739-3821): not judged here
        national = re.sub(r"\D", "", v)
    if national:
        if national[0] in "01" or national[3] in "01":
            out.append("phone-nanp")
        elif national[1] == "9":
            out.append("phone-nanp-reserved")    # N9X area codes are kept for expansion: no number has one
    return out


_LABEL = r"[^\W_](?:[\w-]*[^\W_])?"
_EMAIL = re.compile(rf"[^\s@]+@{_LABEL}(?:\.{_LABEL})*\.[^\W\d_]{{2,63}}")
_RESERVED_DOMAINS = ("example.com", "example.net", "example.org")
_RESERVED_TLDS = ("test", "example", "invalid", "localhost")


def _email(v: str) -> list[str]:
    v = v.strip()
    if not _EMAIL.fullmatch(v):
        return ["email-syntax"]
    domain = v.rsplit("@", 1)[1].lower()
    if domain in _RESERVED_DOMAINS or domain.endswith(tuple("." + d for d in _RESERVED_DOMAINS)) \
            or domain.rsplit(".", 1)[1] in _RESERVED_TLDS:
        return ["email-reserved"]
    return []


def _ip(v: str) -> list[str]:
    try:
        addr = ipaddress.ip_address(v.strip())
    except ValueError:
        return ["ip-parse"]
    return [] if addr.is_global else ["ip-non-public"]


def _bank(v: str) -> list[str]:
    out = []
    if re.search(r"[^\W\d_]", v):
        out.append("bank-letters")
    if not 4 <= len(re.sub(r"\D", "", v)) <= 17:
        out.append("bank-digits")
    return out


CANDIDATES: dict[str, Callable[[str], list[str]]] = {
    "PHONE": _phone, "EMAIL": _email, "IP": _ip, "US_BANK_NUMBER": _bank,
}
EXAMPLES = 5


def reasons(t: str, value: str) -> list[tuple[str, str]]:
    """(reason, shape) for each candidate rule the value fails; empty for a type without candidates."""
    rule = CANDIDATES.get(t)
    return [(r, shape(value)) for r in rule(value)] if rule else []


def audit(samples: Iterable[Sample]) -> dict:
    """dataset -> type -> {total, uncertain, reasons: {reason: {count, examples}}} over the positive gold."""
    out: dict = {}
    for s in samples:
        for sp in s.spans:
            if sp.maisecrets_type not in CANDIDATES or sp.gold not in ("pos", "uncertain"):
                continue
            row = out.setdefault(s.dataset, {}).setdefault(sp.maisecrets_type,
                                                           {"total": 0, "uncertain": 0, "reasons": {}})
            if sp.gold == "uncertain":
                row["uncertain"] += 1
                continue
            row["total"] += 1
            for reason, shp in reasons(sp.maisecrets_type, s.text[sp.start:sp.end]):
                r = row["reasons"].setdefault(reason, {"count": 0, "examples": []})
                r["count"] += 1
                if shp not in r["examples"] and len(r["examples"]) < EXAMPLES:
                    r["examples"].append(shp)
    return out


def report(result: dict) -> str:
    out = ["# Gold audit", "", "Candidate validity rules per type (TASK-30). Counts are over the positive gold; a "
           "value can fail more than one rule. Examples are shapes, never values.", "",
           "| dataset | type | positives | reason | fails | share | example shapes |", "|---|---|---|---|---|---|---|"]
    for ds in sorted(result):
        for t in sorted(result[ds]):
            row = result[ds][t]
            if not row["reasons"]:
                out.append(f"| {ds} | {t} | {row['total']} | none | 0 | 0.00% | |")
            for reason, r in sorted(row["reasons"].items(), key=lambda kv: -kv[1]["count"]):
                share = r["count"] / row["total"] if row["total"] else 0.0
                shapes = ", ".join(f"`{x}`" for x in r["examples"])
                out.append(f"| {ds} | {t} | {row['total']} | {reason} | {r['count']} | {share:.2%} | {shapes} |")
    return "\n".join(out) + "\n"
