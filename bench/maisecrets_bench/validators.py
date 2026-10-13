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


# TASK-11.24: ports of Presidio 2.2.364's validate_result (and invalidate_result for us-npi), recognizer by recognizer.
# Presidio removes "-" and " " before it validates (it-vat-code also "_").
_NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def _clean(v: str, extra: str = "") -> str:
    return re.sub(f"[- {extra}]", "", v.strip())


def es_nif(v: str) -> bool:
    """Spanish NIF (DNI): the letter is NIF_LETTERS[number mod 23]."""
    v = _clean(v).upper()
    digits = "".join(c for c in v if c.isdigit())
    return bool(digits) and v[-1] == _NIF_LETTERS[int(digits) % 23]


def es_nie(v: str) -> bool:
    """Spanish NIE: X, Y or Z (0, 1, 2) before the digits, then the NIF letter of the whole number."""
    v = _clean(v).upper()
    if not v[1:-1].isdigit() or v[:1] not in ("X", "Y", "Z") or not 8 <= len(v) <= 9:
        return False
    return v[-1] == _NIF_LETTERS[int(str("XYZ".index(v[0])) + v[1:-1]) % 23]


def it_vat(v: str) -> bool:
    """Italian partita IVA: a Luhn-like check digit over the first ten; eleven zeros pass the sum but are refused."""
    v = _clean(v, "_")
    if not re.fullmatch(r"\d{11}", v) or v == "0" * 11:
        return False
    x = sum(int(v[2 * i]) for i in range(5))
    y = sum(d - 9 if d > 9 else d for d in (int(v[2 * i + 1]) * 2 for i in range(5)))
    return (10 - (x + y) % 10) % 10 == int(v[10])


def nhs(v: str) -> bool:
    """UK NHS number: digits weighted 10 down to 1, the sum divisible by 11."""
    v = _clean(v)
    return v.isdigit() and sum(int(c) * w for c, w in zip(v, range(10, -1, -1))) % 11 == 0


def us_npi(v: str) -> bool:
    """US NPI: Luhn over 80840 + the ten digits (CMS); a body of one repeated digit is refused."""
    v = _clean(v)
    return v.isdigit() and len(set(v[:-1])) > 1 and _luhn("80840" + v)


def se_org(v: str) -> bool:
    """Swedish organisationsnummer: ten digits, the third at least 2, Luhn."""
    d = re.sub(r"\D", "", v)
    return len(d) == 10 and int(d[2]) >= 2 and _luhn(d)


def uk_vehicle(v: str) -> bool:
    """UK registration plate: in the current format (two letters, age identifier, three letters) the age identifier is
    02-29 or 51-79. Presidio leaves the older prefix and suffix formats unjudged (None), so they pass here."""
    v = _clean(v)
    if len(v) == 7 and v[:2].isalpha() and v[2:4].isdigit():
        age = int(v[2:4])
        return 2 <= age <= 29 or 51 <= age <= 79
    return True


BENCH = {"bench:aba": aba, "bench:it_fiscal": it_fiscal, "bench:se_pnr": se_pnr, "bench:es_nif": es_nif,
         "bench:es_nie": es_nie, "bench:it_vat": it_vat, "bench:nhs": nhs, "bench:us_npi": us_npi,
         "bench:se_org": se_org, "bench:uk_vehicle": uk_vehicle}
