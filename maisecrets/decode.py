"""Decode a base64 or hex run whose bytes are text (TASK-11.26), for the normaliser's decode stage.

The store matches the encoded forms of values it knows; nothing else looks inside an unknown blob. A Kubernetes Secret's
data, a docker config.json auth, an .npmrc _auth or a JWT payload carry a value the shape rules would find in the
clear. A run is decoded when its bytes are UTF-8 text (at least 90% printable); gzip inside base64 is opened, and a run
inside the decoded text is decoded once more (depth 2, no deeper).

Bounded: a run longer than MAX_RUN is not decoded (a whole file, an image), at most MAX_CANDIDATES runs and
MAX_DECODED bytes per text, and no new run after TIME_SLICE seconds. Pure functions, the standard library only."""
from __future__ import annotations

import base64
import binascii
import re
import time
import zlib

MIN_B64 = 24
MIN_HEX = 32
MAX_RUN = 16_384            # encoded characters
MAX_DECODED = 262_144       # bytes per text, over every run and depth
MAX_CANDIDATES = 64         # runs per text
TIME_SLICE = 0.02           # seconds per text
MAX_DEPTH = 2
PRINTABLE = 0.9

# a run of the base64 alphabets (standard and URL-safe) with its padding; hex is a subset and is told apart below
RUN_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{%d,}={0,2}(?![A-Za-z0-9+/=_-])" % min(MIN_B64, MIN_HEX))
_HEX_RE = re.compile(r"(?:[0-9a-fA-F]{2})+")


class Budget:
    """What one text may still spend: candidates, decoded bytes, time."""
    __slots__ = ("candidates", "decoded", "until")

    def __init__(self) -> None:
        self.candidates = MAX_CANDIDATES
        self.decoded = MAX_DECODED
        self.until = time.perf_counter() + TIME_SLICE

    def take(self, n_bytes: int) -> bool:
        if self.candidates <= 0 or n_bytes > self.decoded or time.perf_counter() > self.until:
            return False
        self.candidates -= 1
        self.decoded -= n_bytes
        return True


def _bytes(run: str) -> bytes | None:
    if len(run) >= MIN_HEX and _HEX_RE.fullmatch(run):
        return bytes.fromhex(run)
    if len(run) < MIN_B64:
        return None
    body = run.rstrip("=")
    if ("+" in body or "/" in body) and ("-" in body or "_" in body):
        return None   # two alphabets mixed: an identifier, not an encoding
    if len(body) % 4 == 1:
        return None
    try:
        return base64.b64decode(body.replace("-", "+").replace("_", "/") + "=" * (-len(body) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None


def _text(raw: bytes) -> str | None:
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not s:
        return None
    good = sum(1 for c in s if c.isprintable() or c in "\t\n\r")
    return s if good >= PRINTABLE * len(s) else None


def _gunzip(raw: bytes, budget: Budget) -> bytes | None:
    if raw[:2] != b"\x1f\x8b":
        return None
    try:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        out = d.decompress(raw, budget.decoded)
    except zlib.error:
        return None
    return out if budget.take(len(out)) else None


def decode_run(run: str, depth: int = MAX_DEPTH, budget: Budget | None = None) -> str | None:
    """The text a run encodes, with runs inside it decoded too while depth lasts; None when it is no text."""
    budget = budget or Budget()
    if depth <= 0 or len(run) > MAX_RUN:
        return None
    raw = _bytes(run)
    if raw is None or not budget.take(len(raw)):
        return None
    if depth > 1:
        inner = _gunzip(raw, budget)
        if inner is not None:
            return _text(inner)
    s = _text(raw)
    if s is None or depth <= 1:
        return s
    return decode_text(s, depth - 1, budget)


def decode_text(text: str, depth: int, budget: Budget) -> str:
    """text with each run that encodes text replaced by that text (runs inside decoded at depth - 1)."""
    out: list[str] = []
    pos = 0
    for m in RUN_RE.finditer(text):
        got = decode_run(m.group(0), depth, budget)
        if got is not None:
            out += [text[pos:m.start()], got]
            pos = m.end()
    return "".join(out) + text[pos:] if out else text
