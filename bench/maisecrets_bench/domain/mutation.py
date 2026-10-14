"""Rule mutations (docs/BENCHMARK.md, Judging a change). A mutation is a TOML file:

    name = "Drop the US bank number rule"
    why = "4,117 false alarms on Gretel, few finds"

    [[change]]
    op = "disable"          # disable | set | add
    rule = "us-bank"

    [[change]]
    op = "set"              # set fields: regex, keywords, entropy, score, context, require_context, stopwords,
                            # validator (the detector's, or one of domain/validators.py: "bench:aba"),
                            # allow (regexes on the value that skip a hit, added to the rule's own),
                            # filter (a function of adapters/plugin/filters.py that sees the text around the value)
    rule = "phone"
    regex = "..."

    [[change]]
    op = "add"              # a new rule, after `after` or at the end
    id = "my-token"
    type = "SECRET"
    regex = "..."

    [[change]]
    op = "normalise"        # the shape rules also scan a cleaned copy (maisecrets/normalise.py, TASK-11.25)
    stages = ["ansi", "invisible"]

    [[change]]
    op = "vendored"         # swap the vendored secret rules (TASK-19.3); the other changes apply to the new set
    set = "betterleaks"

    [[change]]
    op = "carry"            # take one rule from a vendored set in place of the rule of that id (TASK-19.8)
    rule = "generic-api-key"
    from = "carried"            # the rules kept from gitleaks (rules/carried.json), or a vendored set

    [[change]]
    op = "unfix"            # switch off one named check that drops hits (detect.FIXES, TASK-26)
    fix = "code-value"
    rule = "ds-keyword-colon"   # optional: without it, every rule that takes the fix loses it

adapters/plugin/mutations.py applies it to a copy of the detector's rule list inside the bench; the plugin is never
edited. judge() compares the scores of a mutated run with the baseline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from . import score
from .bench_error import BenchError


SETTABLE = {"regex", "keywords", "entropy", "score", "context", "require_context", "stopwords", "secret_group",
            "validator", "allow", "filter"}


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


def parse(data: dict, path) -> Mutation:
    """The mutation of a parsed TOML file; `path` names it in the error messages and gives the default name."""
    changes = data.get("change", [])
    if not changes:
        raise BenchError(f"{path}: no [[change]]")
    for c in changes:
        if c.get("op") not in ("disable", "set", "add", "normalise", "unfix", "vendored", "carry"):
            raise BenchError(f"{path}: op {c.get('op')!r} is not disable, set, add, normalise, unfix, vendored "
                             f"or carry")
    return Mutation(data.get("name", PurePath(path).stem), data.get("why", ""), changes)


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
                          "fp": (base[name].fp, mut[name].fp), "found": (base[name].found, mut[name].found),
                          # finds on personal data no type of the plugin's scores (passports, ID cards): TASK-18.2
                          "oos_found": (base[name].oos_found, mut[name].oos_found)}
        if roles.get(name, "scored") == "scored":
            deltas.append(m["score"] - b["score"])
    verdict = "strict" if not reasons else "tolerance" if not beyond else "rejected"
    return {"verdict": verdict, "accepted": verdict != "rejected", "reasons": reasons, "beyond": beyond,
            "datasets": datasets, "overall_delta": sum(deltas) / len(deltas) if deltas else 0.0}
