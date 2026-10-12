"""Valid gold (docs/BENCHMARK.md, TASK-21.6). Datasets carry gold values that are not valid for their type: Gretel
has IBANs that fail mod 97, generators write card numbers that fail Luhn. The detector rightly rejects them, so
counting them as misses would ask a recall floor to be met by weakening the checksums. Each gold positive of a type
with a checksum is checked with the validator the detector uses (the bench's own where the detector has none: ABA,
the SSN shape rules):

- valid: the span, stripped, is the value and passes;
- trimmed: the span holds a label or other text around a value that passes ("IBAN: CH93...", a card block with
  holder, expiry and CVC); the span shrinks to the value;
- invalid: nothing in the span passes; the span becomes gold "uncertain" (neither a miss nor a false alarm).

Setup applies it to every dataset it builds; the counts go into the manifest. Pure functions."""
from __future__ import annotations

import dataclasses
import re
from typing import Callable

from .schema import Sample

REVISION = "valid2"   # valid2 adds CH_AHV and CH_UID (TASK-20); part of every version: a change rebuilds them


def _digits(v: str) -> str:
    return re.sub(r"\D", "", v)


def _ssn_ok(v: str) -> bool:
    d = _digits(v)
    return (len(d) == 9 and d[:3] not in ("000", "666") and d[0] != "9" and d[3:5] != "00"
            and d[5:] != "0000")


def _checks() -> dict[str, tuple[re.Pattern | None, Callable[[str], bool]]]:
    from . import validators
    from .detector import detect
    v = detect.VALIDATORS
    return {
        "IBAN": (re.compile(r"[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}"), detect._iban_ok),
        "CARD": (re.compile(r"\d(?:[ -]?\d){12,18}"), lambda x: 13 <= len(_digits(x)) <= 19 and v["luhn"](x)),
        "US_SSN": (re.compile(r"\d{3}[- ]?\d{2}[- ]?\d{4}"), _ssn_ok),
        "ABA_ROUTING_NUMBER": (re.compile(r"\d{4}-?\d{4}-?\d"), lambda x: len(_digits(x)) == 9
                               and validators.aba(_digits(x))),
        "DE_TAX_ID": (None, v["de_tax_id"]),
        "DE_SOCIAL_SECURITY": (None, v["de_social_security"]),
        "DE_ID_CARD": (None, v["de_id_card"]),
        "DE_VAT_ID": (None, v["de_vat_id"]),
        "DE_HEALTH_INSURANCE": (None, v["de_health_insurance"]),
        "CH_AHV": (re.compile(r"756(?:\.?\d{4}){2}\.?\d{2}"), v["ch_ahv"]),
        "CH_UID": (re.compile(r"CHE[-\s]?\d{3}\.?\d{3}\.?\d{3}"), v["ch_uid"]),
    }


CHECKS = ("IBAN", "CARD", "US_SSN", "ABA_ROUTING_NUMBER", "DE_TAX_ID", "DE_SOCIAL_SECURITY", "DE_ID_CARD",
          "DE_VAT_ID", "DE_HEALTH_INSURANCE", "CH_AHV", "CH_UID")


def _ok(ok: Callable[[str], bool], value: str) -> bool:
    try:
        return bool(ok(value))
    except (ValueError, IndexError, TypeError):
        return False


def check(text: str, start: int, end: int, rx: re.Pattern | None, ok: Callable[[str], bool]):
    """("valid" | "trimmed" | "invalid", start, end): the value's bounds when one passes."""
    value = text[start:end]
    lead = len(value) - len(value.lstrip())
    core = value.strip()
    if (rx is None or rx.fullmatch(core)) and _ok(ok, core):
        return "valid", start, end
    if rx is not None:
        for m in rx.finditer(value):
            # a greedy match can take a character of the text after the value: shrink it from the right
            for stop in range(m.end(), m.start(), -1):
                cand = value[m.start():stop]
                if cand != cand.strip() or not rx.fullmatch(cand):
                    continue
                if _ok(ok, cand):
                    if cand == core:
                        return "valid", start + lead, start + lead + len(core)
                    return "trimmed", start + m.start(), start + stop
    return "invalid", start, end


def mark(samples: list[Sample]) -> tuple[list[Sample], dict]:
    """The samples with checked gold, and dataset -> type -> {pos, valid, invalid, trimmed}."""
    checks = _checks()
    stats: dict[str, dict[str, dict[str, int]]] = {}
    out = []
    for s in samples:
        spans = []
        changed = False
        for sp in s.spans:
            if sp.gold != "pos" or sp.maisecrets_type not in checks:
                spans.append(sp)
                continue
            rx, ok = checks[sp.maisecrets_type]
            verdict, a, b = check(s.text, sp.start, sp.end, rx, ok)
            c = stats.setdefault(s.dataset, {}).setdefault(sp.maisecrets_type,
                                                           {"pos": 0, "valid": 0, "invalid": 0, "trimmed": 0})
            c["pos"] += 1
            c[verdict] += 1
            if verdict == "invalid":
                spans.append(dataclasses.replace(sp, gold="uncertain"))
                changed = True
            elif (a, b) != (sp.start, sp.end):
                spans.append(dataclasses.replace(sp, start=a, end=b))
                changed = True
            else:
                spans.append(sp)
        out.append(dataclasses.replace(s, spans=spans) if changed else s)
    return out, stats
