"""Valid gold (docs/BENCHMARK.md, TASK-21.6). Datasets carry gold values that are not valid for their type: Gretel
has IBANs that fail mod 97, generators write card numbers that fail Luhn. The detector rightly rejects them, so
counting them as misses would ask a recall floor to be met by weakening the checksums. Each gold positive of a type
with a checksum is checked with the validator the detector uses (the bench's own where the detector has none: ABA,
the SSN shape rules):

- valid: the span, stripped, is the value and passes;
- trimmed: the span holds a label or other text around a value that passes ("IBAN: CH93...", a card block with
  holder, expiry and CVC); the span shrinks to the value;
- invalid: nothing in the span passes; the span becomes gold "uncertain" (neither a miss nor a false alarm).

Setup applies it to every dataset it builds; the counts go into the manifest. Pure functions; the validators come in
as an argument (adapters/plugin/gold.py)."""
from __future__ import annotations

import dataclasses
import re
from typing import Callable
from .samples import Sample


REVISION = "valid4"   # valid4: no cut drops a group of the value (TASK-31); a change builds the datasets again


def _digits(v: str) -> str:
    return re.sub(r"\D", "", v)


def _ssn_ok(v: str) -> bool:
    d = _digits(v)
    return (len(d) == 9 and d[:3] not in ("000", "666") and d[0] != "9" and d[3:5] != "00"
            and d[5:] != "0000")


def _valid(t: str) -> Callable[[str], bool]:
    from . import audit
    return lambda value: not audit.reasons(t, value)


# a span with nothing of its type in it is a label error, not a hard value: "[Phone Number]", "adresse e-mail
# professionnelle" (Gretel). It becomes negative: a detector that flags it raises a false alarm (TASK-30)
NOT_THE_TYPE: dict[str, Callable[[str], bool]] = {
    "PHONE": lambda v: not any(c.isdigit() for c in v),
    "EMAIL": lambda v: "@" not in v,
    "IP": lambda v: not any(c.isdigit() for c in v),
}


CHECKS = ("IBAN", "CARD", "US_SSN", "ABA_ROUTING_NUMBER", "DE_TAX_ID", "DE_SOCIAL_SECURITY", "DE_ID_CARD",
          "DE_VAT_ID", "DE_HEALTH_INSURANCE", "CH_AHV", "CH_UID", "PHONE", "EMAIL", "IP", "US_BANK_NUMBER")


def _ok(ok: Callable[[str], bool], value: str) -> bool:
    try:
        return bool(ok(value))
    except (ValueError, IndexError, TypeError):
        return False


# types whose rule is no checksum: a value cut short passes as easily as the whole one ((123) 456-78), so trimming
# takes only a whole match of the pattern (brackets and labels off), never a shorter one
NO_SHRINK = {"PHONE", "EMAIL", "IP"}


_GROUP = re.compile(r"[A-Za-z0-9]+")


def _cut_ok(kept: str, dropped: str) -> bool:
    """A cut drops only what the pattern took after the value: it falls at a separator, and the first group it drops
    differs in length from the last group it keeps (` 12` of an expiry after `1111`). A fake IBAN or card cut at a
    group boundary passes its checksum by chance (1 in 97, 1 in 10): `FR72 2000 7011 5930| 2331 67` or
    `4111 1111 1111 1111| 1234` would leave a fragment no detector reports (TASK-31)."""
    if not dropped or dropped[0].isalnum():
        return False
    last, nxt = _GROUP.findall(kept), _GROUP.findall(dropped)
    return not (last and nxt and len(last[-1]) == len(nxt[0]))


def check(text: str, start: int, end: int, rx: re.Pattern | None, ok: Callable[[str], bool], shrink: bool = True):
    """("valid" | "trimmed" | "invalid", start, end): the value's bounds when one passes."""
    value = text[start:end]
    lead = len(value) - len(value.lstrip())
    core = value.strip()
    if (rx is None or rx.fullmatch(core)) and _ok(ok, core):
        return "valid", start, end
    if rx is not None:
        for m in rx.finditer(value):
            # a greedy match can take a character of the text after the value: shrink it from the right
            for stop in range(m.end(), m.start() if shrink else m.end() - 1, -1):
                cand = value[m.start():stop]
                if cand != cand.strip() or not rx.fullmatch(cand):
                    continue
                if stop < m.end() and not _cut_ok(cand, value[stop:]):
                    continue
                if _ok(ok, cand):
                    if cand == core:
                        return "valid", start + lead, start + lead + len(core)
                    return "trimmed", start + m.start(), start + stop
    return "invalid", start, end


def mark(samples: list[Sample], checks: dict) -> tuple[list[Sample], dict]:
    """The samples with checked gold, and dataset -> type -> {pos, valid, invalid, trimmed}. checks: type ->
    (pattern, validator), the plugin's validators (adapters/plugin/gold.py)."""
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
            c = stats.setdefault(s.dataset, {}).setdefault(sp.maisecrets_type, {
                "pos": 0, "valid": 0, "invalid": 0, "trimmed": 0, "negative": 0, "retyped": 0})
            c["pos"] += 1
            not_the_type = NOT_THE_TYPE.get(sp.maisecrets_type)
            if not_the_type and not_the_type(s.text[sp.start:sp.end]):
                c["negative"] += 1
                spans.append(dataclasses.replace(sp, gold="neg"))
                changed = True
                continue
            verdict, a, b = check(s.text, sp.start, sp.end, rx, ok, sp.maisecrets_type not in NO_SHRINK)
            if verdict == "invalid" and sp.maisecrets_type == "US_BANK_NUMBER":
                # Nemotron labels account numbers in IBAN form (FR76 3000 ..., NL83 INGB ...) as a bank number
                iban, ia, ib = check(s.text, sp.start, sp.end, *checks["IBAN"])
                if iban != "invalid":
                    c["retyped"] += 1
                    spans.append(dataclasses.replace(sp, start=ia, end=ib, maisecrets_type="IBAN"))
                    changed = True
                    continue
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
