"""The recommendations page (TASK-11.14): one markdown page per round for the plugin's owner, built from a baseline
run and the mutation runs judged against it. Counts, rule ids and reasons only, never a value; a local-only dataset
(run.LOCAL_ONLY: ai4privacy) is left out entirely, because the page is meant to be shared."""
from __future__ import annotations

from . import floorscore


def _pct(x) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def page(baseline: dict, mutation_runs: list[dict], local_only: set[str], baseline_id: str) -> str:
    out = [f"# maisecrets: rule recommendations (baseline {baseline_id})", "",
           "Measured with the maisecrets benchmark (`bench/`, docs/BENCHMARK.md) on public labelled datasets. "
           "Every number is a count or a share; no value from a dataset is shown.", "",
           "## Baseline", "", "| dataset | precision | recall | score | true hits | false hits |",
           "|---|---|---|---|---|---|"]
    for name, d in sorted(baseline["datasets"].items()):
        if name in local_only:
            continue
        a = d["all"]
        out.append(f"| {name} | {_pct(a.get('precision'))} | {_pct(a.get('recall'))} | {_pct(a.get('score'))} | "
                   f"{a.get('tp', 0)} | {a.get('fp', 0)} |")
    out += ["", "## Recall floors per type", "", "| type | tier | floor | found / valid gold | lower bound | status |",
            "|---|---|---|---|---|---|"]
    for t, f in sorted(baseline.get("floors", {}).get("types", {}).items()):
        shown = {k: v for k, v in f.get("by_dataset", {}).items() if k not in local_only}
        found, n = sum(v["found"] for v in shown.values()), sum(v["n"] for v in shown.values())
        if not n:
            continue
        # recomputed over the shown datasets: the pooled bound of the run includes the local-only ones
        lower = floorscore.wilson_lower(found, n)
        status = floorscore.status(found, n, f.get("floor"))
        out.append(f"| {t} | {f.get('tier')} | {f.get('floor')} | {found} / {n} | {lower:.4f} | {status} |")
    results = [r for run in mutation_runs for r in run.get("results", [])]
    accepted = [r for r in results if r.get("verdict") == "accepted"]
    out += ["", "## Accepted rule changes", ""]
    if not accepted:
        out += ["None this round.", ""]
    for r in sorted(accepted, key=lambda r: r.get("objective_delta", 0)):
        changes = ", ".join(f"{c.get('op')} `{c.get('rule') or c.get('id') or c.get('set') or c.get('fix')}`"
                            for c in r.get("changes", []))
        out += [f"### {r['name']}", "", f"{r.get('why', '')}", "", f"Changes: {changes}. Weighted false positives "
                f"per 1,000 tokens: {r.get('objective_delta', 0):+.4f}; gaps narrowed: "
                f"{', '.join(r.get('gaps_narrowed') or []) or 'none'}.", "",
                "| dataset | true hits | false hits | precision | recall |", "|---|---|---|---|---|"]
        for name, d in sorted(r.get("datasets", {}).items()):
            if name in local_only:
                continue
            tp, fp = d.get("tp", [0, 0]), d.get("fp", [0, 0])
            out.append(f"| {name} | {tp[0]} -> {tp[1]} | {fp[0]} -> {fp[1]} | {_pct(d['base'].get('precision'))} -> "
                       f"{_pct(d['mutated'].get('precision'))} | {_pct(d['base'].get('recall'))} -> "
                       f"{_pct(d['mutated'].get('recall'))} |")
        out.append("")
    rejected = [r for r in results if r.get("verdict") != "accepted"]
    out += ["## Rejected or neutral", ""]
    for r in rejected:
        why = "; ".join(x for x in r.get("decided_by") or [] if not any(lo in x for lo in local_only)) or "no gain"
        out.append(f"- {r['name']} ({r.get('verdict')}): {why}")
    if not rejected:
        out.append("None.")
    never = baseline.get("never_fired", [])
    out += ["", f"## Rules that never fired ({len(never)})", "", ", ".join(f"`{x}`" for x in sorted(never)) or "None.",
            "", "## Reproduce", "", "```bash", "uv run --project bench python bench/setup.py",
            "uv run --project bench python bench/run.py",
            "uv run --project bench python bench/mutate.py bench/mutations/<round>/*.toml", "```", ""]
    return "\n".join(out)
