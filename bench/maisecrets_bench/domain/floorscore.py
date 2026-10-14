"""Floors first, then false positives (docs/BENCHMARK.md, Judging a change; TASK-21.8). Pure: samples, detections and
the floor table in, numbers out.

summarise() gives, per scoring type (SECRET split in two), the finds over valid in-scope gold pooled over the scored
datasets, the one-sided 95% Wilson lower bound and the floor status; per dataset the false positives per 1,000
whitespace tokens; the weighted objective over the scored datasets; what each guard found and raised; and every miss
of a critical type (positions, no value). verdict() compares two summaries."""
from __future__ import annotations

import math

from . import score
from .samples import OUT_OF_SCOPE

Z = 1.645               # one-sided 95%
EPS = 1e-12
ORDER = {"accepted": 0, "neutral": 1, "rejected": 2}


def wilson_lower(found: int, n: int, z: float = Z) -> float:
    if n == 0:
        return 0.0
    p = found / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / (1 + z * z / n)


def status(found: int, n: int, floor) -> str:
    """clears, gap or too_few for a numeric floor; the floor's own name for no_regression and none."""
    if floor in ("no_regression", "none"):
        return floor
    if n == 0 or found / n < floor - EPS:
        return "gap"
    return "clears" if wilson_lower(found, n) >= floor - EPS else "too_few"


def summarise(samples: list, det: dict, fl, roles: dict, unlabelled_negative: dict | None = None,
              judged: dict | None = None) -> dict:
    unlabelled_negative = unlabelled_negative or {}
    judged = judged or {}
    types: dict[str, dict] = {}
    fp: dict[str, dict] = {}
    guards: dict[str, dict] = {}
    misses = []
    for s in samples:
        ds = det.get((s.dataset, s.sample_id), [])
        role = roles.get(s.dataset, "scored")
        c = score.score_sample(s, ds, unlabelled_negative.get(s.dataset, True), judged.get(s.dataset))
        f = fp.setdefault(s.dataset, {"fp": 0, "tokens": 0, "per_1k": 0.0, "weight": fl.weight(s.dataset),
                                      "role": role})
        f["fp"] += c.fp
        f["tokens"] += len(s.text.split())
        g = guards.setdefault(s.dataset, {"found": 0, "n": 0, "fp": 0}) if role == "guard" else None
        if g is not None:
            g["fp"] += c.fp
        for sp in s.spans:
            if sp.gold != "pos" or sp.maisecrets_type == OUT_OF_SCOPE:
                continue
            hit = any(d.start < sp.end and sp.start < d.end for d in ds)
            if g is not None:
                g["found"] += hit
                g["n"] += 1
                continue
            t = fl.scoring_type(s.dataset, sp.label, sp.maisecrets_type)
            e = types.setdefault(t, {"found": 0, "n": 0, "by_dataset": {}})
            e["found"] += hit
            e["n"] += 1
            bd = e["by_dataset"].setdefault(s.dataset, {"found": 0, "n": 0})
            bd["found"] += hit
            bd["n"] += 1
            if not hit and fl.tier_of(t)[0] == "critical":
                misses.append({"dataset": s.dataset, "sample": s.sample_id, "type": t, "start": sp.start,
                               "end": sp.end})
    for t, e in types.items():
        tier, floor = fl.tier_of(t)
        e.update(tier=tier, floor=floor, recall=e["found"] / e["n"] if e["n"] else None,
                 lower=wilson_lower(e["found"], e["n"]), status=status(e["found"], e["n"], floor))
    weighted = total = 0.0
    for f in fp.values():
        f["per_1k"] = 1000 * f["fp"] / f["tokens"] if f["tokens"] else 0.0
        if f["role"] == "scored" and f["tokens"]:
            weighted += f["weight"] * f["per_1k"]
            total += f["weight"]
    return {"types": dict(sorted(types.items())), "fp": dict(sorted(fp.items())),
            "objective": weighted / total if total else 0.0, "guards": guards, "critical_misses": misses}


def verdict(base: dict, mut: dict) -> dict:
    """accepted, neutral or rejected; decided_by names the type or guard and the datasets that rejected it."""
    decided, narrowed = [], []
    for t, b in base["types"].items():
        m = mut["types"].get(t, {**b, "found": 0, "by_dataset": {}})
        if b["status"] == "none":
            continue
        lost = [ds for ds, v in b["by_dataset"].items()
                if m["by_dataset"].get(ds, {"found": 0})["found"] < v["found"]]
        where = f" (fewer finds on {', '.join(lost)})" if lost else ""
        if b["status"] == "clears":
            if status(m["found"], m["n"], b["floor"]) != "clears":
                decided.append(f"{t}: floor {b['floor']} broken, {b['found']}/{b['n']} -> {m['found']}/{m['n']}{where}")
        elif m["found"] < b["found"]:
            kind = "gap worse" if b["status"] == "gap" else "a find lost"
            decided.append(f"{t}: {kind}, {b['found']}/{b['n']} -> {m['found']}/{m['n']}{where}")
        elif b["status"] == "gap" and m["found"] > b["found"]:
            narrowed.append(t)
    for ds, b in base.get("guards", {}).items():
        m = mut.get("guards", {}).get(ds, b)
        if m["found"] < b["found"] or m["fp"] > b["fp"]:
            decided.append(f"guard {ds}: finds {b['found']} -> {m['found']}, false positives {b['fp']} -> {m['fp']}")
    delta = mut["objective"] - base["objective"]
    v = "rejected" if decided else "accepted" if delta < -EPS or narrowed else "neutral"
    return {"verdict": v, "decided_by": decided, "gaps_narrowed": narrowed, "objective_delta": delta,
            "objective": (base["objective"], mut["objective"])}


def worse(a: str, b: str) -> str:
    return max(a, b, key=ORDER.get)
