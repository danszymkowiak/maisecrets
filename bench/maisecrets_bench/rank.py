"""The leave-one-out ranking (TASK-18.2, decided with the user 2026-10-12). Each removal's counts are marginal: a
find counts as lost only when no other rule picks it up, a false positive as saved only when it disappears.

- protected: the removal breaks a recall floor, worsens a gap or loses a guard; listed, never a candidate.
- pure win: false positives saved and no find lost; sorted by weighted false positives saved.
- trade: finds lost only where the floors allow it (a no-regression type, or a type that still clears its floor);
  sorted by weighted false positives saved per weighted find lost. Lost finds weigh by tier (critical 100, high 10,
  no regression 1), saved false positives by the objective's dataset weights (floors.toml). Fewer than five lost
  finds or saved false positives is flagged as weak evidence.
- no effect: nothing saved, nothing lost.
"""
from __future__ import annotations

from dataclasses import dataclass

TIER_WEIGHT = {"critical": 100.0, "high": 10.0, "default": 1.0}
WEAK = 5
_PROTECTING = ("broken", "gap worse", "guard ")


@dataclass
class Row:
    name: str
    group: str
    fp_saved: int
    weighted_fp_saved: float
    tp_lost: int
    weighted_tp_lost: float
    lost_by_type: dict
    reasons: list

    @property
    def ratio(self) -> float:
        return self.weighted_fp_saved / self.weighted_tp_lost if self.weighted_tp_lost else float("inf")

    @property
    def weak(self) -> bool:
        return (0 < self.tp_lost < WEAK) or (0 < self.fp_saved < WEAK)


def rows(results: list[dict], weights: dict[str, float]) -> list[Row]:
    out = []
    for r in results:
        saved = {d: v["fp"][0] - v["fp"][1] for d, v in r["datasets"].items()}
        lost = {t: f["base"]["found"] - f["mutated"]["found"] for t, f in r.get("floors", {}).items()
                if f["base"]["found"] > f["mutated"]["found"]}
        w_lost = sum(TIER_WEIGHT.get(r["floors"][t]["base"].get("tier"), 0.0) * n for t, n in lost.items())
        w_saved = sum(weights.get(d, 1.0) * n for d, n in saved.items())
        reasons = list(r.get("decided_by", []))
        if any(p in reason for reason in reasons for p in _PROTECTING):
            group = "protected"
        elif lost:
            group = "trade"
        elif sum(saved.values()) > 0:
            group = "pure"
        else:
            group = "none"
        out.append(Row(r["name"], group, sum(saved.values()), w_saved, sum(lost.values()), w_lost, lost, reasons))
    return out


_ORDER = {"pure": 0, "trade": 1, "protected": 2, "none": 3}


def ordered(rs: list[Row]) -> list[Row]:
    def key(r: Row):
        if r.group == "pure":
            return (0, -r.weighted_fp_saved)
        if r.group == "trade":
            return (1, -r.ratio)
        if r.group == "protected":
            return (2, -r.weighted_tp_lost)
        return (3, r.name)
    return sorted(rs, key=key)


def report(rs: list[Row], baseline: str) -> str:
    rs = ordered(rs)
    out = [f"# Leave-one-out ranking (TASK-18.2), baseline {baseline}", "",
           "Counts are marginal (only what no other rule picks up). Weighted false positives use the objective's "
           "dataset weights; lost finds weigh 100 (critical), 10 (high), 1 (no regression). weak: fewer than "
           f"{WEAK} finds lost or false positives saved.", ""]
    groups = [("pure", "Pure wins (false positives saved, no find lost)"),
              ("trade", "Trades (ranked by weighted false positives saved per weighted find lost)"),
              ("protected", "Protected (a floor broken, a gap worse or a guard lost: not candidates)")]
    for g, title in groups:
        sel = [r for r in rs if r.group == g]
        out += [f"## {title}", ""]
        if not sel:
            out += ["None.", ""]
            continue
        out += ["| rule | false positives saved | weighted | finds lost | weighted | ratio | finds lost by type "
                "| note |", "|---|---|---|---|---|---|---|---|"]
        for r in sel:
            ratio = "-" if r.group == "pure" else f"{r.ratio:.1f}"
            types = ", ".join(f"{t} {n}" for t, n in sorted(r.lost_by_type.items())) or "-"
            out.append(f"| {r.name} | {r.fp_saved} | {r.weighted_fp_saved:.0f} | {r.tp_lost} | "
                       f"{r.weighted_tp_lost:.0f} | {ratio} | {types} | {'weak' if r.weak else ''} |")
        out.append("")
    none = [r.name for r in rs if r.group == "none"]
    out += [f"No effect on the datasets: {len(none)} rule(s).", ""]
    return "\n".join(out)
