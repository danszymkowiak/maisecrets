"""Checksums a mutation can give a rule before the plugin has them (`validator = "bench:aba"`). Presidio validates
these recognizers; the plugin's port does not yet, so they rely on a context word alone (detect.PRESIDIO_VALIDATOR)."""
from __future__ import annotations

import re

_IT_ODD = dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                   [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8,
                    12, 14, 16, 10, 22, 25, 24, 23]))


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def aba(v: str) -> bool:
    """ABA routing number: 3, 7, 1 weights, sum divisible by 10."""
    d = re.sub(r"\D", "", v)
    if len(d) != 9:
        return False
    n = [int(c) for c in d]
    return (3 * (n[0] + n[3] + n[6]) + 7 * (n[1] + n[4] + n[7]) + n[2] + n[5] + n[8]) % 10 == 0


def it_fiscal(v: str) -> bool:
    """Italian codice fiscale: the 16th character is the check letter of the first 15."""
    v = v.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{15}[A-Z]", v):
        return False
    total = sum(_IT_ODD[c] if i % 2 == 0 else (int(c) if c.isdigit() else ord(c) - 65) for i, c in enumerate(v[:15]))
    return chr(65 + total % 26) == v[15]


def se_pnr(v: str) -> bool:
    """Swedish personnummer: Luhn over the last ten digits (YYMMDDNNNC)."""
    d = re.sub(r"\D", "", v)
    return len(d) in (10, 12) and _luhn(d[-10:])


BENCH = {"bench:aba": aba, "bench:it_fiscal": it_fiscal, "bench:se_pnr": se_pnr}
