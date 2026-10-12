"""Rule mutations (docs/BENCHMARK.md, Judging a change). A mutation is a TOML file:

    name = "Drop the US bank number rule"
    why = "4,117 false alarms on Gretel, few finds"

    [[change]]
    op = "disable"          # disable | set | add
    rule = "us-bank"

    [[change]]
    op = "set"              # set fields: regex, keywords, entropy, score, context, require_context, stopwords,
                            # validator (the detector's, or one of maisecrets_bench/validators.py: "bench:aba"),
                            # allow (regexes on the value that skip a hit, added to the rule's own),
                            # filter (a function of maisecrets_bench/filters.py that sees the text around the value)
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

It is applied to a copy of the detector's rule list inside the bench; the plugin is never edited. judge() compares
the scores of a mutated run with the baseline."""
from __future__ import annotations

import dataclasses
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import filters, score, validators
from .paths import BenchError

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


def load(path: Path) -> Mutation:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    changes = data.get("change", [])
    if not changes:
        raise BenchError(f"{path}: no [[change]]")
    for c in changes:
        if c.get("op") not in ("disable", "set", "add", "normalise", "unfix", "vendored", "carry"):
            raise BenchError(f"{path}: op {c.get('op')!r} is not disable, set, add, normalise, unfix, vendored "
                             f"or carry")
    return Mutation(data.get("name", Path(path).stem), data.get("why", ""), changes)


def _fields(c: dict, where: str) -> dict:
    from .detector import detect
    out = {}
    for k, v in c.items():
        if k in ("op", "rule", "id", "type", "after"):
            continue
        if k not in SETTABLE:
            raise BenchError(f"{where}: field {k!r} cannot be set (settable: {', '.join(sorted(SETTABLE))})")
        if k == "validator" and v not in detect.VALIDATORS and v not in validators.BENCH:
            raise BenchError(f"{where}: validator {v!r} is not the detector's nor in validators.py")
        if k == "filter":
            if v not in filters.FILTERS:
                raise BenchError(f"{where}: filter {v!r} is not in maisecrets_bench/filters.py")
            out[k] = v
            continue
        if k == "allow":
            out[k] = tuple((re.compile(rx), "secret") for rx in v)
            continue
        out[k] = detect._Lazy(v) if k == "regex" else tuple(v) if isinstance(v, list) else v
    return out


def _stages(c: dict, where: str) -> tuple:
    from . import detector  # noqa: F401  first: the temp home and the plugin on the path
    from maisecrets import normalise
    stages = tuple(c.get("stages", ()))
    unknown = [s for s in stages if s not in normalise.STAGES]
    if unknown or not stages:
        raise BenchError(f"{where}: stage {unknown[0] if unknown else None!r} is not one of "
                         f"{', '.join(normalise.STAGES)}")
    return stages


def validate(m: Mutation) -> None:
    """Every rule a change names exists in some region, and every field can be set. Run once, before the groups."""
    from .detector import rule_index
    known = rule_index()
    for n, c in enumerate(m.changes, 1):
        where = f"{m.name}, change {n}"
        if c["op"] == "normalise":
            _stages(c, where)
            continue
        if c["op"] == "vendored":
            from .detector import detect
            try:
                detect._load_vendored_secrets(str(c.get("set")))
            except ValueError:
                raise BenchError(f"{where}: vendored set {c.get('set')!r} is not one the detector knows") from None
            continue
        if c["op"] == "carry":
            _carried(c, where)
            continue
        if c["op"] == "unfix":
            from .detector import detect
            if c.get("fix") not in detect.FIXES:
                raise BenchError(f"{where}: fix {c.get('fix')!r} is not one of the detector's "
                                 f"({', '.join(detect.FIXES)})")
            if "rule" in c and c["rule"] not in known:
                raise BenchError(f"{where}: rule {c.get('rule')!r} is not a rule of the detector in any region")
            continue
        if c["op"] in ("disable", "set") and c.get("rule") not in known:
            raise BenchError(f"{where}: rule {c.get('rule')!r} is not a rule of the detector in any region")
        if c["op"] in ("set", "add"):
            _fields(c, where)


def ruleset(m: Mutation, base, strict: bool = True):
    """The detector's rule set with the mutation applied (TASK-27): its rules, and the normaliser stages of its last
    `normalise` change (none without one). `base` is not changed; scan() takes the result as `ruleset`."""
    import dataclasses as _dc
    from .detector import detect
    swap = [c["set"] for c in m.changes if c["op"] == "vendored"]
    if swap:
        # the group's own settings (regions, labels) with the other vendored set
        base = detect.build(_dc.replace(detect.settings_from_config(), secret_rules=swap[-1]))
    return detect.RuleSet(tuple(apply(m, list(base.rules), strict)), stages(m))


def _carried(c: dict, where: str):
    """The rule `rule` of the vendored set `from` (or of the carried gitleaks rules: "carried"), as its loader builds it
    (fixes included)."""
    from .detector import detect
    try:
        if c.get("from") == "carried":
            rules = detect._load_carried()
        else:
            rules = detect._load_vendored_secrets(str(c.get("from")))
    except ValueError:
        raise BenchError(f"{where}: vendored set {c.get('from')!r} is not one the detector knows") from None
    rule = next((r for r in rules if r.id == c.get("rule")), None)
    if rule is None:
        raise BenchError(f"{where}: rule {c.get('rule')!r} is not in the vendored set {c.get('from')!r}")
    return rule


def stages(m: Mutation) -> tuple:
    """The normaliser stages the mutation turns on: those of its last `normalise` change, else none."""
    out: tuple = ()
    for n, c in enumerate(m.changes, 1):
        if c["op"] == "normalise":
            out = _stages(c, f"{m.name}, change {n}")
    return out


def apply(m: Mutation, rules: list, strict: bool = True) -> list:
    """A new rule list with the mutation applied; `rules` itself is not changed. With strict=False a change to a rule
    this list does not hold is skipped: the rules differ by region, and us-bank is not in the German group. The
    normaliser stages are not rules: ruleset() carries them."""
    from .detector import detect
    detect.VALIDATORS.update(validators.BENCH)
    filters.install(detect)
    filters.ACTIVE.clear()
    out = list(rules)
    ids = {r.id for r in out}
    for n, c in enumerate(m.changes, 1):
        where = f"{m.name}, change {n}"
        if c["op"] in ("disable", "set") and c.get("rule") not in ids:
            if not strict:
                continue
            raise BenchError(f"{where}: rule {c.get('rule')!r} is not a rule of the detector")
        if c["op"] in ("normalise", "vendored"):
            continue
        elif c["op"] == "carry":
            new = _carried(c, where)
            at = next((i for i, r in enumerate(out) if r.id == new.id), None)
            if at is None:
                out.append(new)
            else:
                out[at] = new
                out = [r for i, r in enumerate(out) if i == at or r.id != new.id]
        elif c["op"] == "unfix":
            out = [dataclasses.replace(r, fixes=tuple(f for f in r.fixes if f != c["fix"]))
                   if c.get("rule") in (None, r.id) else r for r in out]
        elif c["op"] == "disable":
            out = [r for r in out if r.id != c["rule"]]
        elif c["op"] == "set":
            fields = _fields(c, where)
            allow = fields.pop("allow", ())
            if "filter" in fields:
                filters.ACTIVE[c["rule"]] = fields.pop("filter")
            out = [dataclasses.replace(r, **fields, allow_regexes=r.allow_regexes + allow) if r.id == c["rule"] else r
                   for r in out]
        else:
            if c.get("id") in ids:
                raise BenchError(f"{where}: rule {c.get('id')!r} exists already; use op = \"set\"")
            fields = _fields(c, where)
            if "filter" in fields:
                filters.ACTIVE[c["id"]] = fields.pop("filter")
            new = detect.Rule(id=c["id"], type=c["type"], allow_regexes=fields.pop("allow", ()), **fields)
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
                          "fp": (base[name].fp, mut[name].fp), "found": (base[name].found, mut[name].found),
                          # finds on personal data no type of the plugin's scores (passports, ID cards): TASK-18.2
                          "oos_found": (base[name].oos_found, mut[name].oos_found)}
        if roles.get(name, "scored") == "scored":
            deltas.append(m["score"] - b["score"])
    verdict = "strict" if not reasons else "tolerance" if not beyond else "rejected"
    return {"verdict": verdict, "accepted": verdict != "rejected", "reasons": reasons, "beyond": beyond,
            "datasets": datasets, "overall_delta": sum(deltas) / len(deltas) if deltas else 0.0}
