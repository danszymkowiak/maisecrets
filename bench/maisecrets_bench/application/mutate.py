"""Judge mutations against a saved baseline run (docs/BENCHMARK.md, Judging a change). A mutation that only disables
rules re-runs the detector on the samples where one of them fired in the baseline (elsewhere the rule matched
nothing, so nothing can change); any other mutation re-runs every sample.

The verdict is floorscore's (recall floors per type, then weighted false positives per 1,000 tokens); the earlier
strict / within-tolerance verdict comes along as old_verdict, for comparison."""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

from ..domain import floorscore, run_report, score
from ..domain.floors import Floors
from ..domain.mutation import RECALL_TOLERANCE, Mutation, judge
from .ports import BenchPorts


def baseline(ports: BenchPorts, run_dir: Path, parquet: Path) -> tuple[list, dict, list[str]]:
    meta = json.loads(ports.files.read_text(run_dir / "datasets.json"))
    if meta.get("limit"):
        raise ValueError(f"{run_dir} ran with --limit; a baseline must be a full run")
    names = meta["datasets"]
    samples = [s for n in names for s in ports.samples.read(parquet / f"{n}.parquet")]
    return samples, ports.detections.load(run_dir / "detections.parquet"), names


def mutated_detections(ports: BenchPorts, m: Mutation, samples: list, base_det: dict, jobs: int) -> tuple[dict, int]:
    """(detections with the mutation, samples re-run)."""
    if m.disable_only:
        hit = {k for k, ds in base_det.items() if any(d.rule in m.disabled for d in ds)}
        todo = [s for s in samples if (s.dataset, s.sample_id) in hit]
    else:
        todo = samples
    det, _ = ports.detector.detect(todo, jobs, mutation=m) if todo else ({}, {})
    return {**base_det, **{(s.dataset, s.sample_id): det.get((s.dataset, s.sample_id), []) for s in todo}}, len(todo)


def _totals(samples: list, det: dict) -> dict:
    return {name: sum(per.values(), score.Counts()) for name, per in run_report.score_all(samples, det).items()}


def floor_summary(samples: list, det: dict, roles: dict, fl: Floors) -> dict:
    return floorscore.summarise(samples, det, fl, roles, run_report.UNLABELLED_NEGATIVE, run_report.JUDGED)


def evaluate(ports: BenchPorts, mutations: list[Mutation], samples: list, base_det: dict, roles: dict, jobs: int,
             recall_tolerance: float = RECALL_TOLERANCE) -> list[dict]:
    for m in mutations:
        ports.detector.validate(m)
    fl = ports.floors()
    base = _totals(samples, base_det)
    base_fs = floor_summary(samples, base_det, roles, fl)
    out = []
    for m in mutations:
        t0 = time.time()
        det, n = mutated_detections(ports, m, samples, base_det, jobs)
        old = judge(base, _totals(samples, det), roles, recall_tolerance)
        mut_fs = floor_summary(samples, det, roles, fl)
        v = floorscore.verdict(base_fs, mut_fs)
        changed = {t: {"base": base_fs["types"][t], "mutated": mut_fs["types"][t]} for t in base_fs["types"]
                   if base_fs["types"][t]["found"] != mut_fs["types"][t]["found"]}
        out.append({"name": m.name, "why": m.why, "changes": m.changes, "rerun_samples": n,
                    "seconds": time.time() - t0, **old, "old_verdict": old["verdict"], **v,
                    "accepted": v["verdict"] == "accepted", "floors": changed,
                    "fp_per_1k": {ds: (f["per_1k"], mut_fs["fp"][ds]["per_1k"]) for ds, f in base_fs["fp"].items()},
                    "critical_misses": mut_fs["critical_misses"]})
    return sorted(out, key=lambda r: (floorscore.ORDER[r["verdict"]], r["objective_delta"]))


VERDICT_TEXT = {"strict": "accepted", "tolerance": "accepted within tolerance", "rejected": "rejected"}


def _floor_cell(floor) -> str:
    return floor if isinstance(floor, str) else f"{floor:g}"


def report(results: list[dict], baseline_dir: Path, recall_tolerance: float = RECALL_TOLERANCE) -> str:
    notes = run_report.licence_notes(results[0]["datasets"]) if results else []
    out = ["# Rule mutations", "", *notes, "",
           f"Baseline: `{baseline_dir.name}`. Verdict (docs/BENCHMARK.md, Judging a change): rejected when a type "
           "that cleared its recall floor no longer does, a gap gets worse, a no-regression type or a guard loses; "
           "accepted when none of that and the weighted false positives per 1,000 tokens fall or a gap narrows; "
           "else neutral. Ranked by verdict, then by the change of the weighted false positives per 1,000 tokens. "
           f"The earlier verdict (strict; within a recall tolerance of {100 * recall_tolerance:.2f} points) and "
           "the mean score change are shown for comparison.", "",
           "| rank | mutation | verdict | weighted FP/1k change | gaps narrowed | earlier verdict "
           "| mean score change |",
           "|---|---|---|---|---|---|---|"] if results else ["# Rule mutations", "", "none"]
    for i, r in enumerate(results, 1):
        out.append(f"| {i} | {r['name']} | {r['verdict']} | {r['objective_delta']:+.3f} | "
                   f"{', '.join(r['gaps_narrowed']) or '-'} | {VERDICT_TEXT[r['old_verdict']]} | "
                   f"{100 * r['overall_delta']:+.2f} |")
    for r in results:
        out += ["", f"## {r['name']}", "", r["why"] or "", ""]
        out += [f"- {c['op']} `{c.get('rule') or c.get('id')}`" for c in r["changes"]]
        if r["decided_by"]:
            out += ["", "Decided by: " + "; ".join(r["decided_by"])]
        if r["floors"]:
            out += ["", "| type | tier | floor | finds before | finds after | lower bound after | status after |",
                    "|---|---|---|---|---|---|---|"]
            for t, f in r["floors"].items():
                b, m = f["base"], f["mutated"]
                out.append(f"| {t} | {b['tier']} | {_floor_cell(b['floor'])} | {b['found']} / {b['n']} | "
                           f"{m['found']} / {m['n']} | {m['lower']:.4f} | {m['status']} |")
        out += ["", "False positives per 1,000 tokens: " + ", ".join(
            f"{ds} {a:.3f} -> {b:.3f}" for ds, (a, b) in r["fp_per_1k"].items())]
        misses = Counter(m["type"] for m in r["critical_misses"])
        out += ["", "Misses of a critical type after the change (positions in results.json): "
                + (", ".join(f"{t} {n}" for t, n in sorted(misses.items())) or "none") + "."]
        out += ["", "| dataset | TP | FP | found | precision | recall | clean samples |",
                "|---|---|---|---|---|---|---|"]
        for name, d in r["datasets"].items():
            b, m = d["base"], d["mutated"]

            def arrow(key, fmt="{:.2f}%", scale=100):
                if b[key] is None:
                    return "n/a"
                return f"{fmt.format(scale * b[key])} -> {fmt.format(scale * m[key])}"
            out.append(f"| {name} | {d['tp'][0]} -> {d['tp'][1]} | {d['fp'][0]} -> {d['fp'][1]} | "
                       f"{d['found'][0]} -> {d['found'][1]} | {arrow('precision')} | {arrow('recall')} | "
                       f"{arrow('clean_rate')} |")
        if r["reasons"]:
            out += ["", "Worse: " + "; ".join(r["reasons"])]
        if r["beyond"]:
            out += ["", "Rejected: " + "; ".join(r["beyond"])]
        out += ["", f"Re-ran {r['rerun_samples']} samples in {r['seconds']:.0f} s."]
    return "\n".join(out) + "\n"
