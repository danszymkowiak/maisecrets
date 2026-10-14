"""The error export (docs/BENCHMARK.md, Error export): the false positives and the misses of a run, for a person or
an agent to read. Each record holds the rule, the type, the shape of the value (letters as a/A, digits as 9) and the
words before it, where only lowercase words stay readable: a name, a number or a value never does."""
from __future__ import annotations

import re
from collections import Counter

from . import score
from .samples import OUT_OF_SCOPE, Sample

_WORD = re.compile(r"[a-z][a-z'-]*[:=,.;]?")


def shape(v: str) -> str:
    """Letters as A/a and digits as 9, in any script (an accented letter is a letter); runs collapse to X+."""
    v = "".join("9" if ch.isdigit() else ("A" if ch.isupper() else "a") if ch.isalpha() else ch for ch in v)
    v = re.sub(r"\s+", " ", v)
    return re.sub(r"(.)\1+", r"\1+", v)[:24]


def context_before(text: str, start: int, width: int = 40, spans: list | None = None) -> str:
    """The words before `start`: lowercase words as they are, every other token as its shape. A first word the
    window cut is dropped: its lowercase tail ('andskrona,') would show part of a name. A word inside a gold span is
    a shape too, however plain: a password can be a lowercase word."""
    lo = max(0, start - width)
    labelled = [(sp.start, sp.end) for sp in spans or []]
    out = []
    for m in re.finditer(r"\S+", text[lo:start]):
        a, b = lo + m.start(), lo + m.end()
        if a == lo and lo > 0 and not text[lo - 1].isspace():
            continue
        t = m.group()
        inside = any(a < e and s < b for s, e in labelled)
        out.append(t if _WORD.fullmatch(t) and not inside else shape(t))
    return " ".join(out)


def collect(s: Sample, detections: list[score.Detection], unlabelled_negative: bool,
            judged: frozenset | None = None) -> list[dict]:
    base = {"dataset": s.dataset, "split": s.split, "language": s.language, "group": s.group_id}
    out = []
    for d in detections:
        if score.classify(s, d, unlabelled_negative, judged) == "fp":
            out.append({**base, "kind": "fp", "rule": d.rule, "type": d.type, "label": None,
                        "shape": shape(s.text[d.start:d.end]),
                        "context": context_before(s.text, d.start, spans=s.spans)})
    for sp in s.spans:
        if sp.gold != "pos" or sp.maisecrets_type == OUT_OF_SCOPE:
            continue
        if not any(d.start < sp.end and sp.start < d.end for d in detections):
            out.append({**base, "kind": "fn", "rule": None, "type": sp.maisecrets_type, "label": sp.label,
                        "shape": shape(s.text[sp.start:sp.end]),
                        "context": context_before(s.text, sp.start, spans=s.spans)})
    return out


K_SOURCES = 5


def mask_rare(recs: list[dict], k: int = K_SOURCES) -> list[dict]:
    """A context word stays readable only when the contexts of at least k different sources (repository, document)
    hold it: 'routing' and 'password:' do, a value repeated on an unlabelled line of one file does not. The source
    id is dropped from the records."""
    sources: dict[str, set] = {}
    for r in recs:
        for w in set(r["context"].split()):
            sources.setdefault(w, set()).add(r["group"])
    out = []
    for r in recs:
        words = [w if len(sources[w]) >= k or not _WORD.fullmatch(w) else shape(w) for w in r["context"].split()]
        out.append({**{key: v for key, v in r.items() if key != "group"}, "context": " ".join(words)})
    return out


def summary(recs: list[dict], top: int = 5) -> str:
    out = ["# False positives and misses", ""]
    fps = [r for r in recs if r["kind"] == "fp"]
    fns = [r for r in recs if r["kind"] == "fn"]
    for title, rows, key in (("False positives by rule", fps, "rule"), ("Misses by type", fns, "type")):
        out += [f"## {title}", "", f"| {key} | count | datasets | common shapes | common words before |",
                "|---|---|---|---|---|"]
        groups: dict = {}
        for r in rows:
            groups.setdefault(r[key], []).append(r)
        for k, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            shapes = ", ".join(f"`{s}` ({n})" for s, n in Counter(r["shape"] for r in rs).most_common(top))
            words = Counter(w for r in rs for w in r["context"].split()[-3:] if _WORD.fullmatch(w))
            ds = ", ".join(f"{d} {n}" for d, n in Counter(r["dataset"] for r in rs).most_common())
            out.append(f"| {k} | {len(rs)} | {ds} | {shapes} | {', '.join(w for w, _ in words.most_common(top))} |")
        out.append("")
    return "\n".join(out)
