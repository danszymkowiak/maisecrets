"""A mutation applied to the plugin's rules (docs/BENCHMARK.md, Judging a change): checked against every rule of
every region, then applied to a copy of the detector's rule list inside the bench; the plugin is never edited."""
from __future__ import annotations

import dataclasses
import re

from ...domain import validators
from ...domain.bench_error import BenchError
from ...domain.mutation import SETTABLE, Mutation
from . import filters


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
                raise BenchError(f"{where}: filter {v!r} is not in maisecrets_bench/adapters/plugin/filters.py")
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
    `normalise` change (base's stages, the shipped ones, without one). `base` is not changed; scan() takes the result
    as `ruleset`."""
    import dataclasses as _dc
    from .detector import detect
    swap = [c["set"] for c in m.changes if c["op"] == "vendored"]
    if swap:
        # the group's own settings (regions, labels) with the other vendored set
        base = detect.build(_dc.replace(detect.settings_from_config(), secret_rules=swap[-1]))
    return detect.RuleSet(tuple(apply(m, list(base.rules), strict)), stages(m, base.normalise))


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


def stages(m: Mutation, default: tuple = ()) -> tuple:
    """The normaliser stages the mutation runs with: those of its last `normalise` change, else `default`."""
    out: tuple = tuple(default)
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
