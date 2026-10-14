"""A small learned filter for the generic keyword rules (TASK-11.27 b): a logistic regression over about 25 numbers
of a hit (length, character classes, entropy, word coverage, the label's class, quoting, a few shapes, the rule),
trained on the dev split only (bench/learn.py) and kept as a table of coefficients (learned_table.py: numbers, no
value of any dataset). The threshold keeps every find of dev; check decides (bench/round.py judge).

Pure apart from the word list (filters._words) the coverage feature reads."""
from __future__ import annotations

import math

from ...domain import wordlike
from ...domain import entropy
from ...domain import labelclass

RULES = ("generic-api-key", "ds-keyword-colon", "ds-keyword-equal-signs", "ds-basic-auth",
         "ds-keyword-arrow-function-sign-quotes-required", "ds-keyword-quotes-and-semicolon")
NAMES = ("log_len", "digits", "upper", "lower", "special", "entropy", "entropy_norm", "min_entropy", "word_coverage",
         "label_strong", "label_weak", "label_negative", "label_none", "quoted", "slash", "dot", "dash_underscore",
         "template_start", "all_hex", "all_digits", "case_changes", "has_space") + tuple(f"rule:{r}" for r in RULES)

Model = tuple  # (weights, bias, means, scales)


def features(value: str, text: str, start: int, end: int, rule: str) -> list[float]:
    from .detector import detect
    from .filters import _words
    v = value
    n = max(len(v), 1)
    cls = labelclass.classify(detect._label_before(text, start))
    before = text[start - 1:start] if start else ""
    return [
        math.log(n),
        sum(c.isdigit() for c in v) / n,
        sum(c.isupper() for c in v) / n,
        sum(c.islower() for c in v) / n,
        sum(not c.isalnum() for c in v) / n,
        entropy.raw(v),
        entropy.normalised(v),
        entropy.min_entropy(v),
        wordlike.coverage(v, _words()["words"]),
        float(cls == "strong"), float(cls == "weak"), float(cls == "negative"), float(cls == "none"),
        float(before in ("'", '"', "`")),
        float("/" in v), float("." in v), float("-" in v or "_" in v),
        float(v[:1] in ("$", "{", "%", "<")),
        float(all(c in "0123456789abcdefABCDEF" for c in v)),
        float(v.isdigit()),
        sum(a.islower() and b.isupper() for a, b in zip(v, v[1:])) / n,
        float(" " in v),
    ] + [float(rule == r) for r in RULES]


def _standardise(xs: list[list[float]]) -> tuple[list[float], list[float]]:
    k = len(xs[0])
    means = [sum(x[i] for x in xs) / len(xs) for i in range(k)]
    scales = [math.sqrt(sum((x[i] - means[i]) ** 2 for x in xs) / len(xs)) or 1.0 for i in range(k)]
    return means, scales


def _sig(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def prob(model: Model, x: list[float]) -> float:
    w, b, means, scales = model
    return _sig(b + sum(wi * (xi - m) / s for wi, xi, m, s in zip(w, x, means, scales)))


def train(xs: list[list[float]], ys: list[int], epochs: int = 300, rate: float = 0.5, l2: float = 1e-3) -> Model:
    """Batch gradient descent on standardised features, classes weighted to equal mass."""
    means, scales = _standardise(xs)
    zs = [[(xi - m) / s for xi, m, s in zip(x, means, scales)] for x in xs]
    pos = sum(ys) or 1
    neg = (len(ys) - sum(ys)) or 1
    cw = {1: len(ys) / (2 * pos), 0: len(ys) / (2 * neg)}
    k = len(xs[0])
    w = [0.0] * k
    b = 0.0
    for _ in range(epochs):
        gw = [0.0] * k
        gb = 0.0
        for z, y in zip(zs, ys):
            err = (_sig(b + sum(wi * zi for wi, zi in zip(w, z))) - y) * cw[y]
            gb += err
            for i in range(k):
                gw[i] += err * z[i]
        m = len(ys)
        w = [wi - rate * (g / m + l2 * wi) for wi, g in zip(w, gw)]
        b -= rate * gb / m
    return (w, b, means, scales)


def keep_all_threshold(model: Model, finds: list[list[float]]) -> float:
    """The highest threshold that keeps every one of these finds (a hit below it is dropped)."""
    return min(prob(model, x) for x in finds)


def to_table(model: Model, threshold: float, names) -> str:
    w, b, means, scales = model
    rows = "\n".join(f"    ({n!r},\n     {wi!r}, {m!r}, {s!r})," for n, wi, m, s in zip(names, w, means, scales))
    return f"BIAS = {b!r}\nTHRESHOLD = {threshold!r}\nROWS = [  # name, weight, mean, scale\n{rows}\n]\n"


def from_table(table: str) -> tuple[Model, float]:
    ns: dict = {}
    exec(table, ns)   # a table this module wrote: numbers and feature names only
    rows = ns["ROWS"]
    return ([r[1] for r in rows], ns["BIAS"], [r[2] for r in rows], [r[3] for r in rows]), ns["THRESHOLD"]
