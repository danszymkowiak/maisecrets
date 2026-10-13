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


# TASK-11.22: word-likeness, outside a strong label (password123 under a password label stays a hit). The word list
# is SCOWL's american-english (Debian wamerican; SCOWL's permissive licence), read from the system, never bundled;
# MAISECRETS_BENCH_WORDS names another file. 73,133 words, 93 ms to load and 8 MB in /usr/bin/python3 3.12.
# Thresholds chosen on dev of run 20261011-220740: above 0.75 dropped 201 false alarms and no find, above 0.444 kept
# 99.5% of the finds; the bigram threshold 3.092 kept 99.5%.
STRONG_WORDS = {"password", "passwd", "pwd", "secret"}
_WORDS: dict = {}


def _words():
    if not _WORDS:
        import os
        from pathlib import Path
        from . import wordlike
        from .paths import BenchError
        path = Path(os.environ.get("MAISECRETS_BENCH_WORDS", "/usr/share/dict/american-english"))
        if not path.is_file():
            raise BenchError(f"word list {path} not found: install wamerican (SCOWL) or set MAISECRETS_BENCH_WORDS")
        _WORDS["words"] = wordlike.load_words(path)
        _WORDS["bigrams"] = wordlike.bigram_table(_WORDS["words"])
    return _WORDS


def _wordlike(measure: str, threshold: float) -> Filter:
    def keep(value: str, text: str, start: int, end: int) -> bool:
        from . import wordlike
        if _label_words(text, start) & STRONG_WORDS:
            return True
        w = _words()
        got = (wordlike.coverage(value, w["words"]) if measure == "coverage"
               else wordlike.bigram_score(value, w["bigrams"]))
        return got <= threshold
    return keep


_MODEL: list = []
CURRENT_RULE = [""]   # the rule whose hit a filter is judging (allowed() sets it): the learned model reads it


def _learned(value: str, text: str, start: int, end: int) -> bool:
    """TASK-11.27 (b): keep a hit the learned model (learned_table.py, trained on dev) scores at its threshold or
    above."""
    from . import learned
    if not _MODEL:
        from . import learned_table as t
        rows = t.ROWS
        _MODEL.append((([r[1] for r in rows], t.BIAS, [r[2] for r in rows], [r[3] for r in rows]), t.THRESHOLD))
    model, threshold = _MODEL[0]
    rule = CURRENT_RULE[0].split("#", 1)[0]
    return learned.prob(model, learned.features(value, text, start, end, rule)) >= threshold


def label_negative(value: str, text: str, start: int, end: int) -> bool:
    """TASK-11.23: drop a hit whose label is a negative one (token_count, password_hash, tokenizer)."""
    from . import labelclass
    from .detector import detect
    return labelclass.classify(detect._label_before(text, start)) != "negative"


def label_weak_entropy(value: str, text: str, start: int, end: int) -> bool:
    """TASK-11.23: label_negative, and a weak label (key, auth, credential) needs 3 bits of entropy per character."""
    from . import entropy, labelclass
    from .detector import detect
    cls = labelclass.classify(detect._label_before(text, start))
    return cls != "negative" and not (cls == "weak" and entropy.raw(value) < 3.0)


# TASK-11.21: raw entropy per charset, each threshold chosen on dev to keep today's dev share of true positives
# (bench/curves.py, baseline 20261012-194832; normalised entropy picks the same cut, it is raw over a constant)
ENTROPY_BY_CHARSET = {"hex": 3.449, "base32": 3.584, "base62": 3.322, "base64": 3.252, "base64url": 3.426,
                      "printable": 3.594}


def entropy_charset(value: str, text: str, start: int, end: int) -> bool:
    from . import entropy
    return entropy.raw(value) >= ENTROPY_BY_CHARSET[entropy.charset(value)]


FILTERS: dict[str, Filter] = {
    "bench:entropy_charset": entropy_charset,
    "bench:drop_all": lambda value, text, start, end: False,
    "bench:digest_label": digest_label,
    "bench:digest_prefix": digest_prefix,
    "bench:object_id": object_id,
    "bench:digest_any": lambda *a: digest_label(*a) and digest_prefix(*a) and object_id(*a),
    "bench:wordlike_75": _wordlike("coverage", 0.75),
    # TASK-11.22, 2026-10-13: the highest coverage of any find of these rules on the whole bench is 0.871 (one
    # CredData find, outside a strong label; the next is 0.667), so above 0.9 no find is lost. Chosen on all data,
    # not on dev: a thin margin
    "bench:wordlike_90": _wordlike("coverage", 0.9),
    "bench:wordlike_44": _wordlike("coverage", 0.444),
    "bench:bigram_309": _wordlike("bigram", 3.092),
    "bench:label_negative": label_negative,
    # TASK-11.27 (a): a value seen three times or more in one text is a constant (a placeholder, a shared id).
    # Generic rules only: a prefixed token repeated in a log is still a token
    "bench:repeat3": lambda value, text, start, end: text.count(value) < 3,
    "bench:repeat10": lambda value, text, start, end: text.count(value) < 10,   # repeat3 lost 154 finds
    "bench:learned": lambda value, text, start, end: _learned(value, text, start, end),
    "bench:label_weak_entropy": label_weak_entropy,
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
        CURRENT_RULE[0] = rule.id
        return not FILTERS[name](secret, text, start, start + len(secret))
    allowed._bench_filters = True
    detect._allowed = allowed
