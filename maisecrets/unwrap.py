"""Guarded line unwrap (TASK-11.25, AC 3): a secret a terminal or a narrow pane wrapped onto the next line is joined in
a cleaned copy, with a map back to the original, so the redaction covers both lines.

A plain next-line join failed on .env files (README): `API_KEY=…` and the next `DB_HOST=…` became one token. So a
break is removed only when a shape rule (prefix-anchored, no label rule, type SECRET) finds a token across it that the
line before the break does not already hold whole. Pure apart from the detector it asks; off until the bench has
judged it (detect.NORMALISE, stage "unwrap")."""
from __future__ import annotations

import re
from typing import Callable

from .normalise import Normalised

# a break between two token characters, the only place a wrapped token can continue
_BREAK = re.compile(r"(?<=[A-Za-z0-9_+/=.-])\r?\n(?=[A-Za-z0-9_+/=-])")
_TOKEN_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_+/=.-")
# the rules are asked only where the token run before the break has MIN_LEFT characters and both runs together
# MIN_ACROSS (a prefixed token is that long, a pair of words at a break of prose is not), or where that run starts
# right after `=` or `:` (a short password after its label: CredData's wrapped values have halves of 4 to 7). Asking
# at every break cost 517 ms on 120 KB of prose (TASK-37)
MIN_LEFT = 8
MIN_ACROSS = 24

Hits = Callable[[str], list[tuple[int, int]]]


def _shape_secrets(text: str) -> list[tuple[int, int]]:
    from . import detect
    return [(m.start, m.end) for m in detect.scan(text, enabled=detect._shape_rule_ids(), _shapes_only=True)
            if m.type == "SECRET"]


def _line(text: str, a: int, b: int) -> tuple[int, int]:
    """The start of the line that ends at the break [a, b) and the end of the line that follows it."""
    start = text.rfind("\n", 0, a) + 1
    end = text.find("\n", b)
    return start, len(text) if end < 0 else end


def _run(text: str, i: int, step: int, stop: int) -> int:
    """The number of token characters from i on in the direction of step, up to stop and at most MIN_ACROSS."""
    n = 0
    while n < MIN_ACROSS and (i >= stop if step < 0 else i < stop) and text[i] in _TOKEN_CHARS:
        n += 1
        i += step
    return n


def _assigned(text: str, i: int, stop: int) -> bool:
    """The run that starts at i follows `=` or `:` (a quote and spaces between allowed)."""
    i -= 1
    if i >= stop and text[i] in "\"'`":
        i -= 1
    while i >= stop and text[i] in " \t":
        i -= 1
    return i >= stop and text[i] in ":="


def unwrap(text: str, shape_hits: Hits | None = None) -> Normalised:
    if "\n" not in text:
        return Normalised(text)
    hits = shape_hits or _shape_secrets
    joins: list[tuple[int, int]] = []
    for m in _BREAK.finditer(text):
        a, b = m.span()
        ls, le = _line(text, a, b)
        left = text[ls:a]
        tail = _run(text, a - 1, -1, ls)
        if not (tail >= MIN_LEFT and tail + _run(text, b, 1, le) >= MIN_ACROSS or _assigned(text, a - tail, ls)):
            continue
        brk = len(left)
        across = [h for h in hits(left + text[b:le]) if h[0] < brk < h[1]]
        if not across:
            continue
        if any(s <= across[0][0] and e >= brk for s, e in hits(left)):
            continue   # the line before already ends in a whole token: what follows is something else
        joins.append((a, b))
    if not joins:
        return Normalised(text)
    out: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    pos = 0
    for a, b in joins:
        out.append(text[pos:a])
        starts.extend(range(pos, a))
        ends.extend(range(pos + 1, a + 1))
        pos = b
    out.append(text[pos:])
    starts.extend(range(pos, len(text)))
    ends.extend(range(pos + 1, len(text) + 1))
    return Normalised("".join(out), starts, ends)
