"""Precision-recall curves for rules with a score (docs/BENCHMARK.md, Metrics). A relaxed run opens the gates (no
entropy threshold, no context requirement); each candidate keeps its score. A threshold sweep over a rule's
candidates gives its curve: precision against `retained`, the share of the rule's true positives at the lowest
threshold that a threshold keeps. Pure functions; the relaxed run is in bench/curves.py."""
from __future__ import annotations


def sweep(points: list[tuple[float, bool]]) -> list[dict]:
    """points: (score, is_tp) of the judged candidates (true or false positives). One row per distinct threshold."""
    total = sum(1 for _, t in points if t)
    out = []
    for thr in sorted({s for s, _ in points}):
        kept = [t for s, t in points if s >= thr]
        tp = sum(kept)
        fp = len(kept) - tp
        out.append({"threshold": thr, "tp": tp, "fp": fp, "precision": tp / (tp + fp) if kept else 1.0,
                    "retained": tp / total if total else 0.0})
    return out


def auc(curve: list[dict]) -> float | None:
    """Area under precision over retained, from 0 to 1 (trapezoids; flat to 0 at the strictest point). None when the
    rule has no true positive: there is no recall to trade."""
    if not curve or curve[0]["tp"] == 0:
        return None
    pts = sorted((r["retained"], r["precision"]) for r in curve)
    area = pts[0][0] * pts[0][1]
    for (r0, p0), (r1, p1) in zip(pts, pts[1:]):
        area += (r1 - r0) * (p0 + p1) / 2
    return area


def at(curve: list[dict], threshold: float) -> dict:
    """The row a threshold selects: the lowest swept threshold at or above it."""
    for row in curve:
        if row["threshold"] >= threshold:
            return row
    return {"threshold": threshold, "tp": 0, "fp": 0, "precision": 1.0, "retained": 0.0}


def gate_points(points: list[tuple[bool, bool]]) -> dict:
    """points: (context word nearby, is_tp). The rule with its context gate, and without it."""
    def p(rows):
        tp = sum(t for _, t in rows)
        fp = len(rows) - tp
        return {"tp": tp, "fp": fp, "precision": tp / (tp + fp) if rows else 1.0}
    return {"with_context": p([x for x in points if x[0]]), "without_gate": p(points)}
