"""Before a checksum becomes a mutation (TASK-11.24): how many of a rule's hits on labelled gold pass it. The datasets
are generated, and a generator that invents ID numbers often ignores their check digit; a checksum would then drop
true finds. Counts and labels only, never a value."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from . import validators
from .schema import Sample


@dataclass
class Row:
    rule: str
    dataset: str
    validator: str
    gold: int = 0           # hits on a pos span of any label (an unscored ID is a find too)
    gold_pass: int = 0
    other: int = 0          # hits on a neg span or on unlabelled text
    other_pass: int = 0
    labels: Counter = field(default_factory=Counter)


def _on_pos(s: Sample, start: int, end: int):
    for sp in s.spans:
        if sp.gold == "pos" and sp.start < end and start < sp.end:
            return sp
    return None


def table(samples: dict[tuple[str, str], Sample], detections: list[dict], checks: dict[str, str]) -> list[Row]:
    """checks: rule id (without the #n of a pattern) -> a validator of validators.BENCH. Rules with no hit get no
    row; report() lists them."""
    rows: dict[tuple[str, str], Row] = {}
    for d in detections:
        rule = d["rule"].split("#", 1)[0]
        if rule not in checks:
            continue
        s = samples[(d["dataset"], d["sample_id"])]
        ok = validators.BENCH[checks[rule]](s.text[d["start"]:d["end"]])
        r = rows.setdefault((rule, d["dataset"]), Row(rule, d["dataset"], checks[rule]))
        sp = _on_pos(s, d["start"], d["end"])
        if sp is not None:
            r.gold += 1
            r.gold_pass += ok
            r.labels[sp.label] += 1
        else:
            r.other += 1
            r.other_pass += ok
    rows_out = sorted(rows.values(), key=lambda r: (r.rule, r.dataset))
    rows_out.extend(Row(rule, "", v) for rule, v in sorted(checks.items()) if rule not in {r.rule for r in rows_out})
    return rows_out


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "-"


def report(rows: list[Row], baseline: str) -> str:
    out = [f"# Checksum pass rates (baseline {baseline})", "",
           "| rule | dataset | validator | hits on gold | pass | hits elsewhere | pass | gold labels |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r.dataset:
            continue
        labels = ", ".join(f"{k} {v}" for k, v in r.labels.most_common(3))
        out.append(f"| {r.rule} | {r.dataset} | {r.validator} | {r.gold} | {_pct(r.gold_pass, r.gold)} | {r.other} "
                   f"| {_pct(r.other_pass, r.other)} | {labels} |")
    idle = [r.rule for r in rows if not r.dataset]
    if idle:
        out += ["", "No hit on any dataset, so not testable here: " + ", ".join(idle) + "."]
    return "\n".join(out) + "\n"
