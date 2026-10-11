"""Scoring (docs/BENCHMARK.md, What counts and Metrics): detections against gold spans, as counts. Pure: no detector,
no files. Precision counts detections, recall counts gold spans."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .schema import OUT_OF_SCOPE, Sample


@dataclass(frozen=True)
class Detection:
    start: int
    end: int
    type: str
    rule: str


@dataclass
class Counts:
    tp: int = 0             # detections on an in-scope positive
    fp: int = 0             # detections on no positive, where that text is negative
    found: int = 0          # in-scope positives with at least one detection
    fn: int = 0             # in-scope positives with none
    unreviewed: int = 0     # CredData: detections on text no row labels
    unjudged: int = 0       # detections of a type the dataset does not annotate (CredData: all but SECRET)
    lines: int = 0          # lines scanned (for the unreviewed rate)
    oos_found: int = 0      # out-of-scope positives a detection touches anyway
    oos_total: int = 0
    samples: int = 0        # samples scored
    clean: int = 0          # samples without a false positive
    by_type: dict = field(default_factory=dict)     # type -> {tp, fp, found, fn}
    rules: dict = field(default_factory=dict)       # rule -> {hits, tp, fp}
    confusion: dict = field(default_factory=dict)   # (gold type, detected type) -> n, mismatches only

    def __add__(self, o: "Counts") -> "Counts":
        def merge(a: dict, b: dict) -> dict:
            out = {k: dict(v) for k, v in a.items()}
            for k, v in b.items():
                tgt = out.setdefault(k, {kk: 0 for kk in v})
                for kk, n in v.items():
                    tgt[kk] = tgt.get(kk, 0) + n
            return out
        return Counts(self.tp + o.tp, self.fp + o.fp, self.found + o.found, self.fn + o.fn,
                      self.unreviewed + o.unreviewed, self.unjudged + o.unjudged, self.lines + o.lines,
                      self.oos_found + o.oos_found,
                      self.oos_total + o.oos_total, self.samples + o.samples, self.clean + o.clean,
                      merge(self.by_type, o.by_type), merge(self.rules, o.rules),
                      dict(Counter(self.confusion) + Counter(o.confusion)))


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def _bump(d: dict, key: str, field_: str, keys: tuple) -> None:
    d.setdefault(key, {k: 0 for k in keys})[field_] += 1


_TYPE_KEYS = ("tp", "fp", "found", "fn")
_RULE_KEYS = ("hits", "tp", "fp")


def classify(s: Sample, d: Detection, unlabelled_negative: bool, judged: frozenset | None = None) -> str:
    """What one detection is: tp, fp, unjudged, neutral (out-of-scope positive or uncertain) or unreviewed. The rules
    of score_sample, for the error export."""
    def on(gold: str, in_scope: bool | None = None) -> bool:
        return any(sp.gold == gold and (in_scope is None or (sp.maisecrets_type != OUT_OF_SCOPE) == in_scope)
                   and _overlaps(d.start, d.end, sp.start, sp.end) for sp in s.spans)
    if on("pos", True):
        return "tp"
    if judged is not None and d.type not in judged:
        return "unjudged"
    if on("pos", False) or on("uncertain"):
        return "neutral"
    if unlabelled_negative or on("neg"):
        return "fp"
    return "unreviewed"


def score_sample(s: Sample, detections: list[Detection], unlabelled_negative: bool,
                 judged: frozenset | None = None) -> Counts:
    """Counts of one sample. `unlabelled_negative`: text that no span labels is negative (every dataset but CredData,
    where a detection there counts as unreviewed). `judged`: the detected types the dataset annotates (None: all); a
    detection of another type is no error unless it lands on a positive."""
    pos_in = [sp for sp in s.spans if sp.gold == "pos" and sp.maisecrets_type != OUT_OF_SCOPE]
    pos_oos = [sp for sp in s.spans if sp.gold == "pos" and sp.maisecrets_type == OUT_OF_SCOPE]
    neg = [sp for sp in s.spans if sp.gold == "neg"]
    unc = [sp for sp in s.spans if sp.gold == "uncertain"]
    c = Counts(lines=s.text.count("\n") + 1, samples=1)
    confusion: Counter = Counter()

    def hit(spans, d):
        return [sp for sp in spans if _overlaps(d.start, d.end, sp.start, sp.end)]

    for d in detections:
        _bump(c.rules, d.rule, "hits", _RULE_KEYS)
        on_pos = hit(pos_in, d)
        if on_pos:
            c.tp += 1
            gold_type = on_pos[0].maisecrets_type
            _bump(c.by_type, gold_type, "tp", _TYPE_KEYS)
            _bump(c.rules, d.rule, "tp", _RULE_KEYS)
            if gold_type != d.type:
                confusion[(gold_type, d.type)] += 1
        elif judged is not None and d.type not in judged:
            c.unjudged += 1         # CredData says nothing about an e-mail address: neither right nor wrong
        elif hit(pos_oos, d) or hit(unc, d):
            pass                    # a name maisecrets does not claim, or a row CredData left open: no error
        elif unlabelled_negative or hit(neg, d):
            c.fp += 1
            _bump(c.by_type, d.type, "fp", _TYPE_KEYS)
            _bump(c.rules, d.rule, "fp", _RULE_KEYS)
        else:
            c.unreviewed += 1
    for sp in pos_in:
        if any(_overlaps(d.start, d.end, sp.start, sp.end) for d in detections):
            c.found += 1
            _bump(c.by_type, sp.maisecrets_type, "found", _TYPE_KEYS)
        else:
            c.fn += 1
            _bump(c.by_type, sp.maisecrets_type, "fn", _TYPE_KEYS)
    for sp in pos_oos:
        c.oos_total += 1
        c.oos_found += any(_overlaps(d.start, d.end, sp.start, sp.end) for d in detections)
    c.confusion = dict(confusion)
    c.clean = int(c.fp == 0)
    return c


def metrics(c: Counts) -> dict:
    """Precision over detections (1.0 with none), recall over in-scope positives (None without any), F1, the share of
    samples without a false positive, and the dataset score: F1 where there are positives, else that clean rate
    (docs/BENCHMARK.md, Metrics)."""
    precision = c.tp / (c.tp + c.fp) if c.tp + c.fp else 1.0
    recall = c.found / (c.found + c.fn) if c.found + c.fn else None
    f1 = (2 * precision * recall / (precision + recall) if precision + recall else 0.0) if recall is not None \
        else None
    clean_rate = c.clean / c.samples if c.samples else 1.0
    return {"precision": precision, "recall": recall, "f1": f1, "clean_rate": clean_rate,
            "score": f1 if f1 is not None else clean_rate,
            "unreviewed_per_1k_lines": 1000 * c.unreviewed / c.lines if c.lines else 0.0}


def overall(dataset_scores: dict) -> float:
    """The mean of the dataset scores, every dataset weighted equally."""
    return sum(dataset_scores.values()) / len(dataset_scores)
