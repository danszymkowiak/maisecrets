"""Word-likeness of a value (TASK-11.22): a stand-in for token efficiency. A secret is random; an identifier, a
placeholder or a config name is made of words. coverage() is the share of the value's letters inside dictionary
words of three letters or more, after a split on case, separators and digits and a greedy longest-match segmentation
of each chunk. bigram_score() is the mean log-odds of the value's letter bigrams under a table built from the word
list against uniform letters. Pure functions; the word list is loaded by the caller."""
from __future__ import annotations

import math
import re
from collections import Counter


MIN_WORD = 3


MAX_WORD = 20


def chunks(value: str) -> list[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return [c.lower() for c in re.findall(r"[A-Za-z]+", spaced)]


def _covered(chunk: str, words: frozenset) -> int:
    i = n = 0
    while i < len(chunk):
        for j in range(min(len(chunk), i + MAX_WORD), i + MIN_WORD - 1, -1):
            if chunk[i:j] in words:
                n += j - i
                i = j
                break
        else:
            i += 1
    return n


def coverage(value: str, words: frozenset) -> float:
    """Letters inside words over all letters and digits of the value (0 when it has none)."""
    total = sum(ch.isalnum() for ch in value)
    if not total:
        return 0.0
    return sum(_covered(c, words) for c in chunks(value)) / total


def bigram_table(words) -> dict[str, float]:
    """log2 of P(bigram) under the word list over the uniform 1/26**2; unseen bigrams get one count."""
    counts = Counter(w[i:i + 2] for w in words for i in range(len(w) - 1) if w[i:i + 2].isalpha())
    total = sum(counts.values()) + 26 * 26
    uniform = 1 / (26 * 26)
    table = {a + b: math.log2(((counts.get(a + b, 0) + 1) / total) / uniform)
             for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghijklmnopqrstuvwxyz"}
    return table


def bigram_score(value: str, table: dict[str, float]) -> float:
    """The mean log-odds over the letter bigrams of the value's chunks; 0 when there is none."""
    scores = [table[c[i:i + 2]] for c in chunks(value) for i in range(len(c) - 1) if c[i:i + 2] in table]
    return sum(scores) / len(scores) if scores else 0.0


def words_of(text: str, min_len: int = MIN_WORD) -> frozenset:
    """Lowercase ASCII words of at least min_len letters, one per line of a word list (possessives and accents left
    out)."""
    out = set()
    for line in text.splitlines():
        w = line.strip().lower()
        if len(w) >= min_len and w.isascii() and w.isalpha():
            out.add(w)
    return frozenset(out)
