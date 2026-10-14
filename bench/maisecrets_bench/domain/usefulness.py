"""Is a dataset worth keeping (docs/BENCHMARK.md)? Pure functions over the samples and the detections a run saved:
scope, saturation, discrimination (which rules fire where, and whether dropping a rule moves the dataset's score)
and overlap (datasets whose scores always move the same way).

A probe drops a rule's detections and rescores. That is an approximation of removing the rule: in the detector a
removed rule can leave its span to another rule. A real rule change runs the detector again (TASK-11.10)."""
from __future__ import annotations

from itertools import combinations

from . import score
from .run_report import JUDGED, UNLABELLED_NEGATIVE
from .samples import OUT_OF_SCOPE, Sample

Detections = dict   # (dataset, sample_id) -> list[score.Detection]


def rescore(samples: list[Sample], det: Detections, drop: frozenset) -> dict:
    """dataset -> Counts, without the detections of the rules in `drop`."""
    out: dict[str, score.Counts] = {}
    for s in samples:
        ds = [d for d in det.get((s.dataset, s.sample_id), []) if d.rule not in drop]
        c = score.score_sample(s, ds, UNLABELLED_NEGATIVE.get(s.dataset, True), JUDGED.get(s.dataset))
        out[s.dataset] = out.get(s.dataset, score.Counts()) + c
    return out


def table(samples: list[Sample], det: Detections, probes: list[str]) -> dict:
    base = rescore(samples, det, frozenset())
    rules_by_ds = {name: {r for r, v in c.rules.items() if v["hits"]} for name, c in base.items()}
    out = {}
    for name, c in sorted(base.items()):
        spans = [sp for s in samples if s.dataset == name for sp in s.spans if sp.gold == "pos"]
        in_scope = sum(sp.maisecrets_type != OUT_OF_SCOPE for sp in spans)
        others = set().union(*(r for n, r in rules_by_ds.items() if n != name))
        m = score.metrics(c)
        out[name] = {"pos": len(spans), "in_scope_pos": in_scope,
                     "in_scope_share": in_scope / len(spans) if spans else 0.0,
                     "baseline": m,
                     "by_type": {t: score.metrics(score.Counts(tp=v["tp"], fp=v["fp"], found=v["found"], fn=v["fn"]))
                                 for t, v in sorted(c.by_type.items())},
                     "rules_firing": len(rules_by_ds[name]),
                     "rules_only_here": sorted(rules_by_ds[name] - others),
                     "probes": {}}
    for rule in probes:
        after = rescore(samples, det, frozenset({rule}))
        for name in out:
            out[name]["probes"][rule] = score.metrics(after[name])["score"] - out[name]["baseline"]["score"]
    for name in out:
        out[name]["probes_moved"] = sum(1 for d in out[name]["probes"].values() if abs(d) > 1e-12)
    return out


def _sign(x: float) -> int:
    return 0 if abs(x) <= 1e-12 else (1 if x > 0 else -1)


def same_direction(deltas: dict) -> dict:
    """(a, b) -> the share of probes, among those that moved either dataset, that moved both the same way."""
    out = {}
    for a, b in combinations(sorted(deltas), 2):
        moved = [p for p in deltas[a] if _sign(deltas[a][p]) or _sign(deltas[b].get(p, 0.0))]
        same = sum(_sign(deltas[a][p]) == _sign(deltas[b].get(p, 0.0)) for p in moved)
        out[(a, b)] = same / len(moved) if moved else 1.0
    return out
