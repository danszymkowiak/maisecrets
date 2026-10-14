"""Leave-one-out (TASK-18): one disable mutation per rule that fired in a full run. Each is judged like any other
mutation; a rule whose removal is accepted is a removal candidate, and the removals that hurt most show the rules
that earn their place. adapters/files.py writes them into the data directory, never the repository."""
from __future__ import annotations

import json
from .mutation import Mutation


def mutations(metrics: dict) -> list[Mutation]:
    """From a run's metrics.json: the rules with hits, most hits first (ties by id)."""
    fired = sorted(((r, v["hits"]) for r, v in metrics["rules"].items() if v["hits"] > 0), key=lambda x: (-x[1], x[0]))
    return [Mutation(f"Leave out {r}", f"leave-one-out: {n} hits in the baseline",
                     [{"op": "disable", "rule": r}]) for r, n in fired]


def _toml(m: Mutation) -> str:
    out = [f"name = {json.dumps(m.name)}", f"why = {json.dumps(m.why)}"]
    for c in m.changes:
        out += ["", "[[change]]", *(f"{k} = {json.dumps(v)}" for k, v in c.items())]
    return "\n".join(out) + "\n"
