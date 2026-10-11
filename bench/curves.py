#!/usr/bin/env python3
"""Precision-recall curves for the rules with a score (docs/BENCHMARK.md, Metrics):

    uv run --project bench python bench/curves.py [--run <dir>]

Re-runs the detector with the gates open (gitleaks entropy thresholds at 0, Presidio context requirements off),
scores every candidate, and writes curves.md into the run: per entropy rule the area under precision over retained
true positives and the point at today's threshold; per context-gated rule the two points with and without the gate.
In the relaxed run a candidate can claim a span another rule would have taken, so the curves are approximate.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from maisecrets_bench import curves, entropy, run, schema, score, setup
from maisecrets_bench.detector import detect, rule_index
from maisecrets_bench.mutation import Mutation
from maisecrets_bench.paths import BenchError, data_dir


def relaxing(idx: dict) -> tuple[Mutation, set, set]:
    changes, entropy_rules, gated = [], set(), set()
    for rid, d in sorted(idx.items()):
        c = {}
        if d["entropy"]:
            c["entropy"] = 0.0
            entropy_rules.add(rid)
        if d["context"] and (d["score"] < 1.0 or d["require_context"]):
            c.update(score=1.0, require_context=False)
            gated.add(rid)
        if c:
            changes.append({"op": "set", "rule": rid, **c})
    return Mutation("relaxed", "open every gate", changes), entropy_rules, gated


def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def _auc(pts: list, variant: str) -> float | None:
    return curves.auc(curves.sweep([(v[variant], tp) for v, tp in pts]))


def variant_tables(var_pts: list[tuple]) -> list[str]:
    """TASK-11.21: the area per entropy variant and rule, and per charset a threshold for each variant chosen on dev
    (the most precise that keeps today's share of dev true positives), then read on check at that threshold."""
    variants = list(entropy.VARIANTS)
    out = ["", "## Entropy variants (TASK-11.21)", "", "Area under precision over retained, per variant "
           "(raw, over the alphabet's bits, over log2(min(length, alphabet)), min-entropy).", "",
           "| rule | candidates | " + " | ".join(variants) + " |", "|---|---|" + "---|" * len(variants)]
    by_rule: dict[str, list] = {}
    for rule, _, _, v, tp, _ in var_pts:
        by_rule.setdefault(rule, []).append((v, tp))
    for rule in sorted(by_rule, key=lambda r: -len(by_rule[r])):
        pts = by_rule[rule]
        out.append(f"| {rule} | {len(pts)} | " + " | ".join(_pct(_auc(pts, k)) for k in variants) + " |")
    out += ["", "Per charset, over every entropy rule: today is the rules' own raw thresholds; each variant gets one "
            "threshold chosen on dev to keep today's dev share of true positives, then applied to check.", "",
            "| charset | variant | threshold (dev) | dev TP / FP | dev precision | check TP / FP | check precision |",
            "|---|---|---|---|---|---|---|"]
    for cs in sorted({p[2] for p in var_pts}):
        dev = [p for p in var_pts if p[2] == cs and p[1] == "dev"]
        chk = [p for p in var_pts if p[2] == cs and p[1] == "check"]
        if not any(p[4] for p in dev):
            continue
        def today(rows):
            kept = [p for p in rows if p[5]]
            return sum(p[4] for p in kept), sum(not p[4] for p in kept)
        (dtp, dfp), (ctp, cfp) = today(dev), today(chk)
        target = dtp / sum(p[4] for p in dev)
        out.append(f"| {cs} | today | per rule | {dtp} / {dfp} | {_pct(dtp / (dtp + dfp) if dtp + dfp else None)} | "
                   f"{ctp} / {cfp} | {_pct(ctp / (ctp + cfp) if ctp + cfp else None)} |")
        for k in variants:
            row = curves.best(curves.sweep([(p[3][k], p[4]) for p in dev]), target)
            if row is None:
                continue
            kept = [p[4] for p in chk if p[3][k] >= row["threshold"]]
            ktp, kfp = sum(kept), len(kept) - sum(kept)
            out.append(f"| {cs} | {k} | {row['threshold']:.3f} | {row['tp']} / {row['fp']} | "
                       f"{_pct(row['precision'])} | {ktp} / {kfp} | {_pct(ktp / len(kept) if kept else None)} |")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args(argv)
    try:
        manifest = json.loads((setup.default_out() / "manifest.json").read_text(encoding="utf-8"))
        rdir = args.run or run.newest_full_run(data_dir() / "runs", manifest)
        names = json.loads((rdir / "datasets.json").read_text(encoding="utf-8"))["datasets"]
    except BenchError as exc:
        print(f"curves: {exc}", file=sys.stderr)
        return 1
    samples = [s for n in names for s in schema.read(setup.default_out() / f"{n}.parquet")]
    idx = rule_index()
    relax, entropy_rules, gated = relaxing(idx)
    det, _ = run.detect_samples(samples, args.jobs, mutation=relax)
    ent_pts: dict[str, list] = {}
    var_pts: list[tuple] = []    # (rule, split, charset, {variant: value}, is_tp, passes today's gate)
    gate_pts: dict[str, list] = {}
    for s in samples:
        for d in det.get((s.dataset, s.sample_id), []):
            if d.rule not in entropy_rules and d.rule not in gated:
                continue
            kind = score.classify(s, d, run.UNLABELLED_NEGATIVE.get(s.dataset, True), run.JUDGED.get(s.dataset))
            if kind not in ("tp", "fp"):
                continue
            if d.rule in entropy_rules:
                value = s.text[d.start:d.end]
                ent_pts.setdefault(d.rule, []).append((detect.shannon_entropy(value), kind == "tp"))
                var_pts.append((d.rule, s.split, entropy.charset(value),
                                {k: f(value) for k, f in entropy.VARIANTS.items()}, kind == "tp",
                                detect.shannon_entropy(value) >= idx[d.rule]["entropy"]))
            if d.rule in gated:
                window = detect._lower(s.text[max(0, d.start - 80):min(len(s.text), d.end + 40)])
                gate_pts.setdefault(d.rule, []).append((detect._has_context_word(window, tuple(idx[d.rule]["context"])),
                                                        kind == "tp"))
    out = ["# Precision-recall curves", "", *run.licence_notes(names), "",
           f"Relaxed run over {', '.join(names)} (baseline `{rdir.name}`). Approximate: with the gates open a "
           "candidate can take a span another rule would have claimed.", "",
           "## Entropy rules (gitleaks)", "",
           "| rule | threshold today | TP / FP today | precision today | retained today | AUC | best precision "
           "at >= 90% retained |", "|---|---|---|---|---|---|---|"]
    for rid in sorted(ent_pts, key=lambda r: -len(ent_pts[r])):
        c = curves.sweep(ent_pts[rid])
        now = curves.at(c, idx[rid]["entropy"])
        good = [r for r in c if r["retained"] >= 0.9]
        best = max(good, key=lambda r: r["precision"]) if good else None
        best_txt = f"{_pct(best['precision'])} at {best['threshold']:.2f}" if best else "n/a"
        out.append(f"| {rid} | {idx[rid]['entropy']:.2f} | {now['tp']} / {now['fp']} | {_pct(now['precision'])} | "
                   f"{_pct(now['retained'])} | {_pct(curves.auc(c))} | {best_txt} |")
    out += variant_tables(var_pts)
    out += ["", "## Context-gated rules (Presidio): with the gate and without", "",
            "| rule | TP / FP with gate | precision | TP / FP without | precision |", "|---|---|---|---|---|"]
    for rid in sorted(gate_pts, key=lambda r: -len(gate_pts[r])):
        g = curves.gate_points(gate_pts[rid])
        w, wo = g["with_context"], g["without_gate"]
        out.append(f"| {rid} | {w['tp']} / {w['fp']} | {_pct(w['precision'])} | {wo['tp']} / {wo['fp']} | "
                   f"{_pct(wo['precision'])} |")
    out += ["", f"Rules with a score but no judged candidate: {len(entropy_rules - set(ent_pts))} entropy, "
                f"{len(gated - set(gate_pts))} context-gated (n/a)."]
    (rdir / "curves.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:30]))
    print(f"written: {rdir / 'curves.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
