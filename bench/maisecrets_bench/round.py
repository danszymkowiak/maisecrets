"""An agent round (docs/BENCHMARK.md, Dev and check). brief() writes what an agent may read: dev scores, the rules
with the most false alarms and their definitions, the misses by type, masked errors and the mutation format. judge()
scores proposals on dev, then on check; of check only the verdict and the change of the mean come back, so a
proposal cannot be fitted to it."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import errors, mutate, run, schema, score
from .detector import rule_index
from .mutation import RECALL_TOLERANCE, VERDICT_ORDER, Mutation

FORMAT = '''A mutation is a TOML file (one per proposal):

```toml
name = "short name"
why = "what in the errors it answers"

[[change]]
op = "disable"            # disable | set | add
rule = "rule-id"

[[change]]
op = "set"                # fields: regex, keywords, entropy, score, context, require_context, stopwords
rule = "rule-id"
regex = "..."

[[change]]
op = "add"                # a new rule, placed after `after` or at the end
id = "new-id"
type = "SECRET"
regex = "..."
```

Accepted only if no dataset gets worse in recall, precision or clean samples, on dev and on check.'''


def _split_samples(run_dir: Path, parquet: Path, split: str) -> tuple[list, dict]:
    meta = json.loads((run_dir / "datasets.json").read_text(encoding="utf-8"))
    samples = [s for n in meta["datasets"] for s in schema.read(parquet / f"{n}.parquet") if s.split == split]
    return samples, run.load_detections(run_dir / "detections.parquet")


def brief(run_dir: Path, parquet: Path, top: int = 15) -> str:
    samples, det = _split_samples(run_dir, parquet, "dev")
    totals = {n: sum(per.values(), score.Counts()) for n, per in run.score_all(samples, det).items()}
    recs = []
    for s in samples:
        recs += errors.collect(s, det.get((s.dataset, s.sample_id), []), run.UNLABELLED_NEGATIVE.get(s.dataset, True),
                               run.JUDGED.get(s.dataset))
    recs = errors.mask_rare(recs)
    idx = rule_index()
    out = ["# Brief for a rule round (dev split only)", "", "## Dev scores", "",
           "| dataset | TP | FP | found | FN | precision | recall | score |", "|---|---|---|---|---|---|---|---|"]
    for n, c in sorted(totals.items()):
        m = score.metrics(c)
        rec = "n/a" if m["recall"] is None else f"{100 * m['recall']:.1f}%"
        out.append(f"| {n} | {c.tp} | {c.fp} | {c.found} | {c.fn} | {100 * m['precision']:.1f}% | {rec} | "
                   f"{100 * m['score']:.1f}% |")
    fp_rules = Counter(r["rule"] for r in recs if r["kind"] == "fp")
    out += ["", f"## The {top} rules with the most false alarms", ""]
    for rule, n in fp_rules.most_common(top):
        tp = sum(c.rules.get(rule, {}).get("tp", 0) for c in totals.values())
        d = idx.get(rule, {})
        out += [f"### {rule} ({n} false alarms, {tp} true positives on dev)", "", "```json",
                json.dumps(d, indent=1, ensure_ascii=False), "```", ""]
        mine = [r for r in recs if r["kind"] == "fp" and r["rule"] == rule]
        out.append("shapes: " + ", ".join(f"`{s}` ({k})" for s, k in Counter(r["shape"] for r in mine).most_common(6)))
        out.append("words before: " + ", ".join(
            w for w, _ in Counter(w for r in mine for w in r["context"].split()[-3:]).most_common(10)))
        out.append("")
    misses = errors.summary([r for r in recs if r["kind"] == "fn"]).split("## Misses by type")[-1]
    out += ["## Misses by type", "", misses]
    out += ["## Mutation format", "", FORMAT]
    return "\n".join(out) + "\n"


def judge(mutations: list[Mutation], run_dir: Path, parquet: Path, roles: dict, jobs: int,
          recall_tolerance: float = RECALL_TOLERANCE) -> list[dict]:
    """Each proposal on dev and on check; its verdict is the worse of the two."""
    out = []
    dev, det = _split_samples(run_dir, parquet, "dev")
    check, _ = _split_samples(run_dir, parquet, "check")
    dev_r = {r["name"]: r for r in mutate.evaluate(mutations, dev, det, roles, jobs, recall_tolerance)}
    check_r = {r["name"]: r for r in mutate.evaluate(mutations, check, det, roles, jobs, recall_tolerance)}
    for m in mutations:
        d, c = dev_r[m.name], check_r[m.name]
        verdict = max(d["verdict"], c["verdict"], key=VERDICT_ORDER.get)
        out.append({"name": m.name, "why": m.why, "dev": d,
                    "check": {"verdict": c["verdict"], "accepted": c["accepted"], "overall_delta": c["overall_delta"]},
                    "verdict": verdict, "accepted": verdict != "rejected"})
    return sorted(out, key=lambda r: (VERDICT_ORDER[r["verdict"]], -r["dev"]["overall_delta"]))
