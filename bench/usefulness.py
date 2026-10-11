#!/usr/bin/env python3
"""Is each dataset worth keeping (docs/BENCHMARK.md)? Reads a run (default: the newest) and its data, drops each of
the most-firing rules in turn (a probe) and reports scope, saturation, discrimination and overlap per dataset:

    uv run --project bench python bench/usefulness.py [--run <dir>] [--probes 30]

Writes usefulness.md into the run. The keep or drop decision is the user's.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from maisecrets_bench import run, schema, setup, usefulness
from maisecrets_bench.paths import BenchError, data_dir

SATURATED = 0.99        # a score at or above this leaves no room to show an improvement
OVERLAP = 0.95          # probes moving two datasets the same way this often: one adds little


def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def verdicts(t: dict, same: dict) -> dict:
    out = {}
    for name, d in t.items():
        why = []
        if d["in_scope_pos"] == 0:
            why.append("no in-scope positives: it measures false alarms only")
        if d["baseline"]["score"] >= SATURATED:
            why.append(f"saturated (score {_pct(d['baseline']['score'])})")
        if d["probes_moved"] == 0:
            why.append("no probe moves its score")
        for (a, b), share in same.items():
            if name in (a, b) and share >= OVERLAP:
                why.append(f"moves like {b if name == a else a} on {_pct(share)} of the probes")
        out[name] = ("drop candidate" if why else "keep", why)
    return out


def render(t: dict, same: dict, probes: list[str]) -> str:
    v = verdicts(t, same)
    out = ["# Is each dataset worth keeping?", "",
           "| dataset | positives | in scope | score | precision | recall | clean samples | rules firing | "
           "only here | probes that move it | verdict |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, d in t.items():
        b = d["baseline"]
        out.append(f"| {name} | {d['pos']} | {d['in_scope_pos']} ({_pct(d['in_scope_share'])}) | {_pct(b['score'])} | "
                   f"{_pct(b['precision']) if b['recall'] is not None else 'n/a'} | {_pct(b['recall'])} | "
                   f"{_pct(b['clean_rate'])} | {d['rules_firing']} | "
                   f"{len(d['rules_only_here'])} | {d['probes_moved']} of {len(probes)} | {v[name][0]} |")
    out += ["", "## Why", ""]
    out += [f"- **{name}**: {'; '.join(why) if why else 'in scope, not saturated, moved by probes'}"
            for name, (_, why) in v.items()]
    out += ["", "## Overlap (share of probes moving both the same way)", ""]
    out += [f"- {a} / {b}: {_pct(share)}" for (a, b), share in same.items()]
    out += ["", "## Saturated types (precision and recall at or above 99%)", ""]
    for name, d in t.items():
        sat = [ty for ty, m in d["by_type"].items() if m["recall"] is not None and m["precision"] >= SATURATED
               and m["recall"] >= SATURATED]
        out.append(f"- {name}: {', '.join(sat) or 'none'}")
    out += ["", f"## Probe deltas (score change when the rule's detections are dropped; {len(probes)} rules)", "",
            "| rule | " + " | ".join(t) + " |", "|---|" + "---|" * len(t)]
    for rule in probes:
        out.append(f"| {rule} | " + " | ".join(f"{100 * t[n]['probes'][rule]:+.2f}" for n in t) + " |")
    out += ["", "A probe drops a rule's detections and rescores; in the detector another rule could then claim the "
                "span, so a probe approximates removing the rule."]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, help="a run directory (default: the newest)")
    ap.add_argument("--probes", type=int, default=30, help="how many of the most-firing rules to probe")
    args = ap.parse_args(argv)
    try:
        runs = sorted((data_dir() / "runs").glob("*/detections.parquet"))
        if not args.run and not runs:
            raise BenchError("no run with saved detections; run bench/run.py first")
        rdir = args.run or runs[-1].parent
        meta = json.loads((rdir / "datasets.json").read_text(encoding="utf-8"))
        if meta.get("limit"):
            raise BenchError(f"{rdir} ran with --limit; the check needs a full run")
        samples = [s for name in meta["datasets"] for s in schema.read(setup.default_out() / f"{name}.parquet")]
        det = run.load_detections(rdir / "detections.parquet")
        hits: dict[str, int] = {}
        for ds in det.values():
            for d in ds:
                hits[d.rule] = hits.get(d.rule, 0) + 1
        probes = sorted(hits, key=lambda r: -hits[r])[:args.probes]
        t = usefulness.table(samples, det, probes)
        same = usefulness.same_direction({n: d["probes"] for n, d in t.items()})
    except BenchError as exc:
        print(f"usefulness: {exc}", file=sys.stderr)
        return 1
    text = render(t, same, probes)
    (rdir / "usefulness.md").write_text(text, encoding="utf-8")
    print(text.split("\n## Overlap")[0])
    print(f"written: {rdir / 'usefulness.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
