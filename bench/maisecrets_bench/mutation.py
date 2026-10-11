"""Rule mutations (docs/BENCHMARK.md, Judging a change). A mutation is a TOML file:

    name = "Drop the US bank number rule"
    why = "4,117 false alarms on Gretel, few finds"

    [[change]]
    op = "disable"          # disable | set | add
    rule = "us-bank"

    [[change]]
    op = "set"              # set fields of a rule: regex, keywords, entropy, score, context, require_context, stopwords
    rule = "phone"
    regex = "..."

    [[change]]
    op = "add"              # a new rule, after `after` or at the end
    id = "my-token"
    type = "SECRET"
    regex = "..."

It is applied to a copy of the detector's rule list inside the bench; the plugin is never edited. judge() compares
the scores of a mutated run with the baseline."""
from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import score
from .paths import BenchError

SETTABLE = {"regex", "keywords", "entropy", "score", "context", "require_context", "stopwords", "secret_group"}
EPS = 1e-12
RECALL_TOLERANCE = 0.005    # half a point of recall (docs/BENCHMARK.md, Judging a change)
VERDICT_ORDER = {"strict": 0, "tolerance": 1, "rejected": 2}


@dataclass(frozen=True)
class Mutation:
    name: str
    why: str
    changes: list

    @property
    def disable_only(self) -> bool:
        return all(c["op"] == "disable" for c in self.changes)

    @property
    def disabled(self) -> set:
        return {c["rule"] for c in self.changes if c["op"] == "disable"}


def load(path: Path) -> Mutation:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    changes = data.get("change", [])
    if not changes:
        raise BenchError(f"{path}: no [[change]]")
    for c in changes:
        if c.get("op") not in ("disable", "set", "add"):
            raise BenchError(f"{path}: op {c.get('op')!r} is not disable, set or add")
    return Mutation(data.get("name", Path(path).stem), data.get("why", ""), changes)


def _fields(c: dict, where: str) -> dict:
    from .detector import detect
    out = {}
    for k, v in c.items():
        if k in ("op", "rule", "id", "type", "after"):
            continue
        if k not in SETTABLE:
            raise BenchError(f"{where}: field {k!r} cannot be set (settable: {', '.join(sorted(SETTABLE))})")
        out[k] = detect._Lazy(v) if k == "regex" else tuple(v) if isinstance(v, list) else v
    return out


def validate(m: Mutation) -> None:
    """Every rule a change names exists in some region, and every field can be set. Run once, before the groups."""
    from .detector import rule_index
    known = rule_index()
    for n, c in enumerate(m.changes, 1):
        where = f"{m.name}, change {n}"
        if c["op"] in ("disable", "set") and c.get("rule") not in known:
            raise BenchError(f"{where}: rule {c.get('rule')!r} is not a rule of the detector in any region")
        if c["op"] in ("set", "add"):
            _fields(c, where)


def apply(m: Mutation, rules: list, strict: bool = True) -> list:
    """A new rule list with the mutation applied; `rules` itself is not changed. With strict=False a change to a rule
    this list does not hold is skipped: the rules differ by region, and us-bank is not in the German group."""
    from .detector import detect
    out = list(rules)
    ids = {r.id for r in out}
    for n, c in enumerate(m.changes, 1):
        where = f"{m.name}, change {n}"
        if c["op"] in ("disable", "set") and c.get("rule") not in ids:
            if not strict:
                continue
            raise BenchError(f"{where}: rule {c.get('rule')!r} is not a rule of the detector")
        if c["op"] == "disable":
            out = [r for r in out if r.id != c["rule"]]
        elif c["op"] == "set":
            fields = _fields(c, where)
            out = [dataclasses.replace(r, **fields) if r.id == c["rule"] else r for r in out]
        else:
            if c.get("id") in ids:
                raise BenchError(f"{where}: rule {c.get('id')!r} exists already; use op = \"set\"")
            new = detect.Rule(id=c["id"], type=c["type"], **_fields(c, where))
            at = next((i + 1 for i, r in enumerate(out) if r.id == c.get("after")), len(out))
            out.insert(at, new)
        ids = {r.id for r in out}
    return out


def _worse(name: str, b: dict, m: dict) -> list[str]:
    out = []
    if b["recall"] is not None and m["recall"] < b["recall"] - EPS:
        out.append(f"{name}: recall {100 * b['recall']:.2f}% -> {100 * m['recall']:.2f}%")
    if b["recall"] is not None and m["precision"] < b["precision"] - EPS:
        out.append(f"{name}: precision {100 * b['precision']:.2f}% -> {100 * m['precision']:.2f}%")
    if m["clean_rate"] < b["clean_rate"] - EPS:
        out.append(f"{name}: clean samples {100 * b['clean_rate']:.2f}% -> {100 * m['clean_rate']:.2f}%")
    return out


def _beyond_tolerance(name: str, b: dict, m: dict, tol: float) -> list[str]:
    out = []
    if m["score"] < b["score"] - EPS:
        out.append(f"{name}: score {100 * b['score']:.2f}% -> {100 * m['score']:.2f}%")
    if b["recall"] is not None and m["recall"] < b["recall"] - tol - EPS:
        out.append(f"{name}: recall {100 * b['recall']:.2f}% -> {100 * m['recall']:.2f}%, beyond the tolerance")
    return out


def judge(base: dict, mut: dict, roles: dict, recall_tolerance: float = RECALL_TOLERANCE) -> dict:
    """verdict "strict" when no dataset gets worse in recall, precision (where it has positives) or clean samples;
    "tolerance" when it is not strict but on every dataset the score does not fall and recall falls by at most
    recall_tolerance; else "rejected". A guard dataset counts for that but not in the mean. reasons: why it is not
    strict; beyond: why it is rejected. overall_delta: the change of the mean score of the scored datasets."""
    reasons, beyond, datasets, deltas = [], [], {}, []
    for name in sorted(base):
        b, m = score.metrics(base[name]), score.metrics(mut[name])
        reasons += _worse(name, b, m)
        beyond += _beyond_tolerance(name, b, m, recall_tolerance)
        datasets[name] = {"role": roles.get(name, "scored"), "base": b, "mutated": m,
                          "score_delta": m["score"] - b["score"], "tp": (base[name].tp, mut[name].tp),
                          "fp": (base[name].fp, mut[name].fp), "found": (base[name].found, mut[name].found)}
        if roles.get(name, "scored") == "scored":
            deltas.append(m["score"] - b["score"])
    verdict = "strict" if not reasons else "tolerance" if not beyond else "rejected"
    return {"verdict": verdict, "accepted": verdict != "rejected", "reasons": reasons, "beyond": beyond,
            "datasets": datasets, "overall_delta": sum(deltas) / len(deltas) if deltas else 0.0}
