"""Filters a mutation can stack on a rule (`filter = "bench:name"`, docs/BENCHMARK.md, Judging a change). A filter
gets the value, the text and the value's offsets, so it can read the label before the value; it returns True to keep
the hit. It runs inside detect.scan after the rule's validator, entropy, context and allowlist, and before the hit
claims its span, so a dropped hit leaves the span to the next rule as a failed validator would. The plugin is not
edited: the bench wraps detect._allowed in the worker."""
from __future__ import annotations

from typing import Callable

Filter = Callable[[str, str, int, int], bool]

FILTERS: dict[str, Filter] = {
    "bench:drop_all": lambda value, text, start, end: False,
}
ACTIVE: dict[str, str] = {}     # rule id -> filter name, set by mutation.apply in each process


def _value_start(text: str, m, secret: str) -> int:
    """scan() does not hand its offsets to _allowed: the value is the first occurrence of it from the match on (a
    value that scan moved past the match, the next-line case, is found the same way)."""
    i = text.find(secret, m.start())
    return i if i >= 0 else m.start()


def install(detect) -> None:
    """Wrap detect._allowed once per process."""
    if getattr(detect._allowed, "_bench_filters", False):
        return
    original = detect._allowed

    def allowed(rule, text, m, secret):
        if original(rule, text, m, secret):
            return True
        name = ACTIVE.get(rule.id)
        if name is None:
            return False
        start = _value_start(text, m, secret)
        return not FILTERS[name](secret, text, start, start + len(secret))
    allowed._bench_filters = True
    detect._allowed = allowed
