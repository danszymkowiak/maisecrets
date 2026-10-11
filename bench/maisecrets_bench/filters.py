"""Filters a mutation can stack on a rule (`filter = "bench:name"`, docs/BENCHMARK.md, Judging a change). A filter
gets the value, the text and the value's offsets, so it can read the label before the value; it returns True to keep
the hit. It runs inside detect.scan after the rule's validator, entropy, context and allowlist, and before the hit
claims its span, so a dropped hit leaves the span to the next rule as a failed validator would. The plugin is not
edited: the bench wraps detect._allowed in the worker."""
from __future__ import annotations

import re
from typing import Callable

Filter = Callable[[str, str, int, int], bool]

# TASK-11.20: digests, integrity strings and object ids, dropped only by what the text says they are
_HEX = re.compile(r"[0-9a-fA-F]+")
DIGEST_HEX_LENGTHS = {32, 40, 56, 64, 96, 128}
DIGEST_WORDS = {"hash", "sha", "sha1", "sha256", "sha384", "sha512", "md5", "md5sum", "sha256sum", "checksum",
                "digest", "integrity", "etag", "commit", "rev", "revision", "fingerprint", "oid"}
SECRET_WORDS = {"secret", "password", "passwd", "pwd", "token", "key", "apikey", "auth", "credential", "credentials"}
_PREFIX = r"(?:sha(?:1|256|384|512)[-:]|h1:)"
_STARTS, _ENDS = re.compile(_PREFIX, re.I), re.compile(_PREFIX + "$", re.I)


def _label_words(text: str, start: int) -> set[str]:
    """The last three words before the value on its line (camelCase and snake_case split), lowercase."""
    line = text[max(text.rfind("\n", 0, start) + 1, start - 40):start]
    line = re.sub(r"([a-z])([A-Z])", r"\1 \2", line)
    return {w.lower() for w in re.findall(r"[A-Za-z]+[0-9]*", line)[-3:]}


def digest_label(value: str, text: str, start: int, end: int) -> bool:
    words = _label_words(text, start)
    is_digest = (len(value) in DIGEST_HEX_LENGTHS and _HEX.fullmatch(value) is not None
                 and bool(words & DIGEST_WORDS) and not words & SECRET_WORDS)
    return not is_digest


def digest_prefix(value: str, text: str, start: int, end: int) -> bool:
    return not (_STARTS.match(value) or _ENDS.search(text[max(0, start - 8):start]))


def object_id(value: str, text: str, start: int, end: int) -> bool:
    if len(value) != 24 or not _HEX.fullmatch(value):
        return True
    called = re.search(r"ObjectId\(\s*[\"']?$", text[max(0, start - 12):start]) is not None
    words = _label_words(text, start)
    return not (called or ({"id", "oid", "objectid"} & words and not words & SECRET_WORDS))


FILTERS: dict[str, Filter] = {
    "bench:drop_all": lambda value, text, start, end: False,
    "bench:digest_label": digest_label,
    "bench:digest_prefix": digest_prefix,
    "bench:object_id": object_id,
    "bench:digest_any": lambda *a: digest_label(*a) and digest_prefix(*a) and object_id(*a),
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
