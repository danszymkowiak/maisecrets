"""A bench run's scores and report (docs/BENCHMARK.md, Metrics): the language groups, which datasets are judged how,
the counts per dataset, split, tag and rule, and the markdown report. Counts and rule ids, never a value."""
from __future__ import annotations

from collections import Counter
from . import score
from .samples import Sample


# regions and locale per sample language (docs/BENCHMARK.md, Regions); `generic` is always on. A language without
# a Presidio region of its own runs the generic rules only
LANGUAGES = {
    "en": (["us", "uk"], "en_US"), "de": (["de"], "de_DE"), "es": (["es"], "es_ES"), "it": (["it"], "it_IT"),
    "fr": ([], "fr_FR"), "nl": ([], "nl_NL"), "sv": (["se"], "sv_SE"), "und": ([], "en_US"),
}


# a locale whose country has rules of its own runs in a group of its own (TASK-28): findocs' Swiss documents run with
# region ch, every other sample keeps its language's group
LOCALES = {"de_CH": (["ch"], "de_CH"), "fr_CH": (["ch"], "fr_CH"), "it_CH": (["ch"], "it_CH")}


SKIP_TYPES = {"HIDDEN"}     # removal of invisible characters: no detection to score


# where text no span labels is negative; CredData labels candidate lines only (docs/BENCHMARK.md, CredData)
UNLABELLED_NEGATIVE = {"creddata": False}


# left out of a default run: TAB is saturated and out of scope (docs/BENCHMARK.md, user decision 2026-10-11)
DROPPED = {"tab"}


# a dataset that guards: a change must not make it worse, but it has no weight in the overall mean. The generated
# tool output is ours, so tuning to it would be circular (docs/BENCHMARK.md, Synthetic tool output)
# kagglepii: real essays, but only 45 values in scope (2026-10-13): its weight would be noise, its false-alarm rate on
# real text is what it adds (TASK-11.36)
GUARD = {"synthetic", "kagglepii"}


def default_roles(names) -> dict:
    return {n: "guard" for n in names if n in GUARD}


# a dataset whose results stay local; its note goes into every report that includes it
LOCAL_ONLY = {"ai4privacy": "ai4privacy: academic and non-commercial use only (AI4Privacy licence). Local "
                            "measurement; leave it out of anything sent upstream. The plugin's owner needs "
                            "AI4Privacy's permission first (licensing@ai4privacy.com). Its precision is a lower "
                            "bound: its generator also wrote values outside the labelled slots (TASK-33)."}


def default_datasets(manifest: dict) -> list[str]:
    return sorted(set(manifest.get("datasets", {})) - DROPPED)


# a CC BY dataset: its attribution goes into every report that includes it
ATTRIBUTION = {"nemotron": "nemotron: NVIDIA, Nemotron-PII (huggingface.co/datasets/nvidia/Nemotron-PII), CC BY 4.0.",
               "mendeley": "mendeley: Synthetic Dataset for PII Detection and Anonymization in Financial Documents, "
                           "Mendeley Data, doi 10.17632/tzrjx692jy.1, CC BY 4.0.",
               "kagglepii": "kagglepii: PIILO, The Learning Agency Lab (the data of Kaggle's PII Data Detection "
                            "competition), CC BY 4.0."}


def licence_notes(names) -> list[str]:
    return [f"> {LOCAL_ONLY.get(n) or ATTRIBUTION[n]}" for n in sorted(names) if n in LOCAL_ONLY or n in ATTRIBUTION]


# the detected types a dataset annotates; a detection of another type there is neither right nor wrong. CredData
# labels credentials only; the others label personal data broadly and judge every type
JUDGED = {"creddata": frozenset({"SECRET"})}


def group_of(s: Sample) -> str:
    """The sample's group: its language, or language:locale for a locale in LOCALES (de:de_CH)."""
    loc = next((t.split(":", 1)[1] for t in s.tags if t.startswith("locale:")), None)
    return f"{s.language}:{loc}" if loc in LOCALES else s.language


def _group_config(group: str) -> tuple[list[str], str]:
    """(regions, locale) a group runs with."""
    lang, _, loc = group.partition(":")
    return LOCALES[loc] if loc else LANGUAGES[lang]


def score_all(samples: list[Sample], det: dict) -> dict:
    """dataset -> split -> Counts."""
    results: dict[str, dict[str, score.Counts]] = {}
    for s in samples:
        c = score.score_sample(s, det.get((s.dataset, s.sample_id), []), UNLABELLED_NEGATIVE.get(s.dataset, True),
                               JUDGED.get(s.dataset))
        per = results.setdefault(s.dataset, {})
        per[s.split] = per.get(s.split, score.Counts()) + c
    return results


def _counts_json(c: score.Counts) -> dict:
    return {"tp": c.tp, "fp": c.fp, "found": c.found, "fn": c.fn, "unreviewed": c.unreviewed, "unjudged": c.unjudged,
            "lines": c.lines,
            "oos_found": c.oos_found, "oos_total": c.oos_total, "samples": c.samples, "clean": c.clean,
            **score.metrics(c),
            "by_type": {t: {**v, **score.metrics(score.Counts(tp=v["tp"], fp=v["fp"], found=v["found"],
                                                                    fn=v["fn"]))}
                        for t, v in sorted(c.by_type.items())},
            "confusion": [{"gold": g, "detected": d, "n": n} for (g, d), n in sorted(c.confusion.items())]}


def score_tags(samples: list[Sample], det: dict) -> dict:
    """dataset -> tag -> Counts, for the samples that carry tags."""
    out: dict[str, dict[str, score.Counts]] = {}
    for s in samples:
        if not s.tags:
            continue
        c = score.score_sample(s, det.get((s.dataset, s.sample_id), []), UNLABELLED_NEGATIVE.get(s.dataset, True),
                               JUDGED.get(s.dataset))
        per = out.setdefault(s.dataset, {})
        for t in s.tags:
            per[t] = per.get(t, score.Counts()) + c
    return out


def summarise(results: dict, groups: dict, tags: dict | None = None) -> dict:
    datasets = {}
    all_rules: dict[str, dict] = {}
    for name, per_split in sorted(results.items()):
        total = sum(per_split.values(), score.Counts())
        datasets[name] = {"all": _counts_json(total), **{sp: _counts_json(c) for sp, c in sorted(per_split.items())}}
        if (tags or {}).get(name):
            datasets[name]["tags"] = {t: _counts_json(c) for t, c in sorted(tags[name].items())}
        for rule, v in total.rules.items():
            agg = all_rules.setdefault(rule, {"hits": 0, "tp": 0, "fp": 0, "by_dataset": {}})
            for k in ("hits", "tp", "fp"):
                agg[k] += v[k]
            agg["by_dataset"][name] = v
    active = sorted({r for g in groups.values() for r in g["rules"]})
    scores = {name: d["all"]["score"] for name, d in datasets.items() if name not in GUARD}
    return {"datasets": datasets, "overall": score.overall(scores) if scores else None, "scores": scores,
            "rules": dict(sorted(all_rules.items())),
            "never_fired": [r for r in active if r not in all_rules],
            "groups": {lang: {k: v for k, v in g.items() if k != "rules"} | {"rules": len(g["rules"])}
                       for lang, g in groups.items()}}


def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def report(summary: dict, manifest: dict, seconds: float) -> str:
    """The markdown report: counts, rates and rule ids only."""
    guards = sorted(n for n in summary["datasets"] if n in GUARD)
    out = ["# maisecrets rule benchmark", "", *licence_notes(summary["datasets"]), "",
           f"Overall score (equal weight over the scored datasets): **{_pct(summary['overall'])}**. "
           f"Run time {seconds:.0f} s." + (f" Guards, not in the mean: {', '.join(guards)}." if guards else ""), "",
           "| dataset | version | TP | FP | found | FN | precision | recall | F1 | clean samples | score |"
           " unreviewed /1k lines | out-of-scope touched |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, d in summary["datasets"].items():
        a = d["all"]
        ver = manifest.get("datasets", {}).get(name, {}).get("version", "?")[:10]
        precision = _pct(a["precision"]) if a["recall"] is not None else "n/a"   # no positives: no precision
        out.append(f"| {name} | {ver} | {a['tp']} | {a['fp']} | {a['found']} | {a['fn']} | {precision} | "
                   f"{_pct(a['recall'])} | {_pct(a['f1'])} | {_pct(a['clean_rate'])} | {_pct(a['score'])} | "
                   f"{a['unreviewed_per_1k_lines']:.2f} | "
                   f"{a['oos_found']} of {a['oos_total']} |")
    for name, d in summary["datasets"].items():
        out += ["", f"## {name}", "", "| type | TP | FP | found | FN | precision | recall |",
                "|---|---|---|---|---|---|---|"]
        for t, v in d["all"]["by_type"].items():
            out.append(f"| {t} | {v['tp']} | {v['fp']} | {v['found']} | {v['fn']} | {_pct(v['precision'])} | "
                       f"{_pct(v['recall'])} |")
        if d.get("tags"):
            out += ["", "| tag | samples | TP | FP | FN | precision | recall | score |",
                    "|---|---|---|---|---|---|---|---|"]
            for t, v in d["tags"].items():
                out.append(f"| {t} | {v['samples']} | {v['tp']} | {v['fp']} | {v['fn']} | {_pct(v['precision'])} | "
                           f"{_pct(v['recall'])} | {_pct(v['score'])} |")
        splits = [sp for sp in ("dev", "check") if sp in d]
        out += ["", "split: " + ", ".join(f"{sp} score {_pct(d[sp]['score'])}" for sp in splits)]
        if d["all"]["confusion"]:
            out += ["", "type mismatches (gold -> detected): " +
                    ", ".join(f"{c['gold']} -> {c['detected']} ({c['n']})" for c in d["all"]["confusion"])]
    if summary.get("floors"):
        out += floor_report(summary["floors"])
    top = sorted(summary["rules"].items(), key=lambda kv: -kv[1]["hits"])[:30]
    out += ["", "## Rules by hits (top 30)", "", "| rule | hits | TP | FP |", "|---|---|---|---|"]
    out += [f"| {r} | {v['hits']} | {v['tp']} | {v['fp']} |" for r, v in top]
    out += ["", f"## Rules that never fired ({len(summary['never_fired'])})", "",
            ", ".join(summary["never_fired"]) or "none"]
    out += ["", "## Groups", "", "| language | samples | regions | label languages | rules |", "|---|---|---|---|---|"]
    out += [f"| {lang} | {g['samples']} | {', '.join(g['regions'])} | {', '.join(g['languages'])} | {g['rules']} |"
            for lang, g in summary["groups"].items()]
    out += ["", "CredData values are obfuscated with their shape kept; a checksum or entropy rule can behave a little "
                "differently on them than on real values."]
    return "\n".join(out) + "\n"


def _floor_cell(floor) -> str:
    return floor if isinstance(floor, str) else f"{floor:g}"


def floor_report(fs: dict) -> list[str]:
    """Recall per scoring type against its floor, false positives per 1,000 tokens, and the critical misses."""
    out = ["", "## Recall floors (valid gold, scored datasets pooled)", "",
           "| type | tier | floor | finds | recall | lower bound | status |", "|---|---|---|---|---|---|---|"]
    order = {"critical": 0, "high": 1, "default": 2, "none": 3}
    for t, e in sorted(fs["types"].items(), key=lambda kv: (order.get(kv[1]["tier"], 9), kv[0])):
        out.append(f"| {t} | {e['tier']} | {_floor_cell(e['floor'])} | {e['found']} / {e['n']} | "
                   f"{_pct(e['recall'])} | {_pct(e['lower'])} | {e['status']} |")
    out += ["", f"Weighted false positives per 1,000 tokens (scored datasets): **{fs['objective']:.3f}**.", "",
            "| dataset | role | weight | false positives | tokens | false positives per 1,000 tokens |",
            "|---|---|---|---|---|---|"]
    for ds, f in fs["fp"].items():
        out.append(f"| {ds} | {f['role']} | {f['weight']:g} | {f['fp']} | {f['tokens']} | {f['per_1k']:.3f} |")
    counts = fs.get("critical_miss_counts") or Counter(m["type"] for m in fs.get("critical_misses", []))
    out += ["", "Misses of a critical type (positions in critical_misses.tsv): "
            + (", ".join(f"{t} {n}" for t, n in sorted(counts.items())) or "none") + "."]
    return out


def critical_misses_tsv(fs: dict) -> str:
    rows = ["dataset\tsample\ttype\tstart\tend"]
    rows += [f"{m['dataset']}\t{m['sample']}\t{m['type']}\t{m['start']}\t{m['end']}" for m in fs["critical_misses"]]
    return "\n".join(rows) + "\n"
