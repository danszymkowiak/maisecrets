"""Judge mutations against a saved baseline run (docs/BENCHMARK.md, Judging a change). A mutation that only disables
rules re-runs the detector on the samples where one of them fired in the baseline (elsewhere the rule matched
nothing, so nothing can change); any other mutation re-runs every sample."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import run, schema
from .mutation import RECALL_TOLERANCE, VERDICT_ORDER, Mutation, judge


def baseline(run_dir: Path, parquet: Path) -> tuple[list, dict, list[str]]:
    meta = json.loads((run_dir / "datasets.json").read_text(encoding="utf-8"))
    if meta.get("limit"):
        raise ValueError(f"{run_dir} ran with --limit; a baseline must be a full run")
    names = meta["datasets"]
    samples = [s for n in names for s in schema.read(parquet / f"{n}.parquet")]
    return samples, run.load_detections(run_dir / "detections.parquet"), names


def mutated_detections(m: Mutation, samples: list, base_det: dict, jobs: int) -> tuple[dict, int]:
    """(detections with the mutation, samples re-run)."""
    if m.disable_only:
        hit = {k for k, ds in base_det.items() if any(d.rule in m.disabled for d in ds)}
        todo = [s for s in samples if (s.dataset, s.sample_id) in hit]
    else:
        todo = samples
    det, _ = run.detect_samples(todo, jobs, mutation=m) if todo else ({}, {})
    return {**base_det, **{(s.dataset, s.sample_id): det.get((s.dataset, s.sample_id), []) for s in todo}}, len(todo)


def _totals(samples: list, det: dict) -> dict:
    return {name: sum(per.values(), run.score.Counts()) for name, per in run.score_all(samples, det).items()}


def evaluate(mutations: list[Mutation], samples: list, base_det: dict, roles: dict, jobs: int,
             recall_tolerance: float = RECALL_TOLERANCE) -> list[dict]:
    from .mutation import validate
    for m in mutations:
        validate(m)
    base = _totals(samples, base_det)
    out = []
    for m in mutations:
        t0 = time.time()
        det, n = mutated_detections(m, samples, base_det, jobs)
        j = judge(base, _totals(samples, det), roles, recall_tolerance)
        out.append({"name": m.name, "why": m.why, "changes": m.changes, "rerun_samples": n,
                    "seconds": time.time() - t0, **j})
    return sorted(out, key=lambda r: (VERDICT_ORDER[r["verdict"]], -r["overall_delta"]))


VERDICT_TEXT = {"strict": "accepted", "tolerance": "accepted within tolerance", "rejected": "rejected"}


def report(results: list[dict], baseline_dir: Path, recall_tolerance: float = RECALL_TOLERANCE) -> str:
    notes = run.licence_notes(results[0]["datasets"]) if results else []
    out = ["# Rule mutations", "", *notes, "",
           f"Baseline: `{baseline_dir.name}`. Accepted: no dataset worse in recall, precision or clean samples. "
           f"Accepted within tolerance: on every dataset the score does not fall and recall falls by at most "
           f"{100 * recall_tolerance:.2f} points. Ranked by verdict, then by the change of the mean score of the "
           "scored datasets.", "",
           "| rank | mutation | verdict | mean score change | " + " | ".join(results[0]["datasets"]) + " |",
           "|---|---|---|---|" + "---|" * len(results[0]["datasets"])] if results else ["# Rule mutations", "", "none"]
    for i, r in enumerate(results, 1):
        cells = []
        for name, d in r["datasets"].items():
            tag = " (guard)" if d["role"] == "guard" else ""
            cells.append(f"{100 * d['score_delta']:+.2f}{tag}")
        out.append(f"| {i} | {r['name']} | {VERDICT_TEXT[r['verdict']]} | "
                   f"{100 * r['overall_delta']:+.2f} | " + " | ".join(cells) + " |")
    for r in results:
        out += ["", f"## {r['name']}", "", r["why"] or "", ""]
        out += [f"- {c['op']} `{c.get('rule') or c.get('id')}`" for c in r["changes"]]
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
