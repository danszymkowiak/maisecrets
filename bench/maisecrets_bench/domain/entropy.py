"""Entropy variants for the gate of the entropy rules (TASK-11.21). Raw Shannon entropy rises with the length and the
alphabet of a value, so one threshold per rule treats a 20-character hex value and a 60-character base64 value
alike. The variants: raw bits per character; raw over the bits of the value's alphabet (hex 4, base32 5, base62
about 5.95, base64 6); raw over the most a value of that length can reach, log2(min(length, alphabet)); and
min-entropy, -log2 of the share of the most frequent character. Pure functions."""
from __future__ import annotations

import math
import string
from collections import Counter
from typing import Callable

_HEX = set(string.hexdigits)
_B32 = set(string.ascii_uppercase + "234567=")
_B62 = set(string.ascii_letters + string.digits)
_B64 = _B62 | set("+/=")
_B64URL = _B62 | set("-_=")
SIZES = {"hex": 16, "base32": 32, "base62": 62, "base64": 64, "base64url": 64, "printable": 95}


def charset(value: str) -> str:
    """The smallest alphabet of hex, base32, base62, base64, base64url that holds the value, else printable."""
    chars = set(value)
    for name, alpha in (("hex", _HEX), ("base32", _B32), ("base62", _B62), ("base64", _B64), ("base64url", _B64URL)):
        if chars <= alpha:
            return name
    return "printable"


def raw(value: str) -> float:
    if not value:
        return 0.0
    n = len(value)
    return -sum(c / n * math.log2(c / n) for c in Counter(value).values())


def normalised(value: str) -> float:
    return raw(value) / math.log2(SIZES[charset(value)])


def length_corrected(value: str) -> float:
    top = math.log2(min(len(value), SIZES[charset(value)])) if value else 0.0
    return raw(value) / top if top > 0 else 0.0


def min_entropy(value: str) -> float:
    if not value:
        return 0.0
    return -math.log2(max(Counter(value).values()) / len(value))


VARIANTS: dict[str, Callable[[str], float]] = {"raw": raw, "normalised": normalised,
                                                "length_corrected": length_corrected, "min": min_entropy}
