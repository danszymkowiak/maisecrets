"""The validators valid gold is checked with (docs/BENCHMARK.md, TASK-21.6): the detector's own, and the bench's
where the detector has none. domain/validgold.py takes them as an argument."""
from __future__ import annotations

import re
from typing import Callable

from ...domain.validgold import _digits, _ssn_ok, _valid


def checks() -> dict[str, tuple[re.Pattern | None, Callable[[str], bool]]]:
    from ...domain import validators
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
        # the types without a checksum: the validity rules the gold audit chose (audit.py, TASK-30)
        "PHONE": (re.compile(r"\+?\(?\d[\d ().-]*\d(?:\s*(?:ext\.?|x)\s*\d{1,6})?"), _valid("PHONE")),
        "EMAIL": (re.compile(r"[^\s@\[\]<>()\"']+@[^\s@\[\]<>()\"']+"), _valid("EMAIL")),
        "IP": (re.compile(r"[0-9A-Fa-f:.]*[0-9A-Fa-f]"), _valid("IP")),
        "US_BANK_NUMBER": (None, _valid("US_BANK_NUMBER")),    # a letter prefix (C82376415) is part of the id
    }
