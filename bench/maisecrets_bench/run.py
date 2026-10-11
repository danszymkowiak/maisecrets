"""Run the detector over the benchmark data and score it (docs/BENCHMARK.md, Metrics). The imperative shell around
score.py: samples are grouped by language, each group runs in worker processes whose maisecrets home, regions and
locale fit that language, so a run is the same on every machine. Results hold counts and rule ids, never a value."""
from __future__ import annotations

import json
import os
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import schema, score
from .schema import Sample

# regions and locale per sample language (docs/BENCHMARK.md, Regions); `generic` is always on. A language without
# a Presidio region of its own runs the generic rules only
LANGUAGES = {
    "en": (["us", "uk"], "en_US"), "de": (["de"], "de_DE"), "es": (["es"], "es_ES"), "it": (["it"], "it_IT"),
    "fr": ([], "fr_FR"), "nl": ([], "nl_NL"), "sv": (["se"], "sv_SE"), "und": ([], "en_US"),
}
SKIP_TYPES = {"HIDDEN"}     # removal of invisible characters: no detection to score
# where text no span labels is negative; CredData labels candidate lines only (docs/BENCHMARK.md, CredData)
UNLABELLED_NEGATIVE = {"creddata": False}

_detect = None


def _init_worker(regions: list[str], locale: str) -> None:
    """A fresh home with the test store and the group's regions; the locale fixed. Runs before maisecrets loads."""
    global _detect
    home = Path(tempfile.mkdtemp(prefix="maisecrets-bench-run-"))
    (home / "config.json").write_text(json.dumps({"backend": "jsonfile", "allow_plaintext_store": True,
                                                  "regions": regions}))
    os.environ["MAISECRETS_HOME"] = str(home)
    os.environ["MAISECRETS_LOCALE"] = locale
    from . import detector
    _detect = detector.detect


def _detections(text: str) -> list[score.Detection]:
    return [score.Detection(m.start, m.end, m.type, m.kind) for m in _detect.scan(text) if m.type not in SKIP_TYPES]


def _score_chunk(chunk: list[Sample]) -> list[tuple[str, str, score.Counts]]:
    out = []
    for s in chunk:
        c = score.score_sample(s, _detections(s.text), UNLABELLED_NEGATIVE.get(s.dataset, True))
        out.append((s.dataset, s.split, c))
    return out


def _active(regions: list[str], locale: str) -> dict:
    """The rules, regions and label languages a group runs with, from a worker of its own."""
    with ProcessPoolExecutor(1, initializer=_init_worker, initargs=(regions, locale)) as ex:
        return ex.submit(_describe).result()


def _describe() -> dict:
    a = _detect.active_regions()
    return {"regions": list(a.regions), "languages": list(a.languages),
            "rules": sorted({r.id for r in _detect.rules()})}


def score_samples(samples: list[Sample], jobs: int, chunk: int = 50) -> tuple[dict, dict]:
    """(dataset -> split -> Counts, language -> what it ran with)."""
    by_lang: dict[str, list[Sample]] = {}
    for s in samples:
        by_lang.setdefault(s.language, []).append(s)
    results: dict[str, dict[str, score.Counts]] = {}
    groups = {}
    for lang, group in sorted(by_lang.items()):
        regions, locale = LANGUAGES[lang]
        groups[lang] = {**_active(regions, locale), "samples": len(group)}
        group.sort(key=lambda s: -len(s.text))      # the long files first: no straggler at the end
        chunks = [group[i:i + chunk] for i in range(0, len(group), chunk)]
        with ProcessPoolExecutor(jobs, initializer=_init_worker, initargs=(regions, locale)) as ex:
            for part in ex.map(_score_chunk, chunks):
                for dataset, split, c in part:
                    per = results.setdefault(dataset, {})
                    per[split] = per.get(split, score.Counts()) + c
    return results, groups


def _counts_json(c: score.Counts) -> dict:
    return {"tp": c.tp, "fp": c.fp, "found": c.found, "fn": c.fn, "unreviewed": c.unreviewed, "lines": c.lines,
            "oos_found": c.oos_found, "oos_total": c.oos_total, "samples": c.samples, "clean": c.clean,
            **score.metrics(c),
            "by_type": {t: {**v, **score.metrics(score.Counts(tp=v["tp"], fp=v["fp"], found=v["found"],
                                                                    fn=v["fn"]))}
                        for t, v in sorted(c.by_type.items())},
            "confusion": [{"gold": g, "detected": d, "n": n} for (g, d), n in sorted(c.confusion.items())]}


def summarise(results: dict, groups: dict) -> dict:
    datasets = {}
    all_rules: dict[str, dict] = {}
    for name, per_split in sorted(results.items()):
        total = sum(per_split.values(), score.Counts())
        datasets[name] = {"all": _counts_json(total), **{sp: _counts_json(c) for sp, c in sorted(per_split.items())}}
        for rule, v in total.rules.items():
            agg = all_rules.setdefault(rule, {"hits": 0, "tp": 0, "fp": 0, "by_dataset": {}})
            for k in ("hits", "tp", "fp"):
                agg[k] += v[k]
            agg["by_dataset"][name] = v
    active = sorted({r for g in groups.values() for r in g["rules"]})
    scores = {name: d["all"]["score"] for name, d in datasets.items()}
    return {"datasets": datasets, "overall": score.overall(scores) if scores else None, "scores": scores,
            "rules": dict(sorted(all_rules.items())),
            "never_fired": [r for r in active if r not in all_rules],
            "groups": {lang: {k: v for k, v in g.items() if k != "rules"} | {"rules": len(g["rules"])}
                       for lang, g in groups.items()}}


def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def report(summary: dict, manifest: dict, seconds: float) -> str:
    """The markdown report: counts, rates and rule ids only."""
    out = ["# maisecrets rule benchmark", "",
           f"Overall score (equal weight over datasets): **{_pct(summary['overall'])}**. Run time {seconds:.0f} s.", "",
           "| dataset | version | TP | FP | found | FN | precision | recall | F1 | clean samples | score |"
           " unreviewed /1k lines | out-of-scope touched |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, d in summary["datasets"].items():
        a = d["all"]
        ver = manifest.get("datasets", {}).get(name, {}).get("version", "?")[:10]
        out.append(f"| {name} | {ver} | {a['tp']} | {a['fp']} | {a['found']} | {a['fn']} | {_pct(a['precision'])} | "
                   f"{_pct(a['recall'])} | {_pct(a['f1'])} | {_pct(a['clean_rate'])} | {_pct(a['score'])} | "
                   f"{a['unreviewed_per_1k_lines']:.2f} | "
                   f"{a['oos_found']} of {a['oos_total']} |")
    for name, d in summary["datasets"].items():
        out += ["", f"## {name}", "", "| type | TP | FP | found | FN | precision | recall |",
                "|---|---|---|---|---|---|---|"]
        for t, v in d["all"]["by_type"].items():
            out.append(f"| {t} | {v['tp']} | {v['fp']} | {v['found']} | {v['fn']} | {_pct(v['precision'])} | "
                       f"{_pct(v['recall'])} |")
        splits = [sp for sp in ("dev", "check") if sp in d]
        out += ["", "split: " + ", ".join(f"{sp} score {_pct(d[sp]['score'])}" for sp in splits)]
        if d["all"]["confusion"]:
            out += ["", "type mismatches (gold -> detected): " +
                    ", ".join(f"{c['gold']} -> {c['detected']} ({c['n']})" for c in d["all"]["confusion"])]
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


def run(parquet: Path, datasets: list[str], out: Path, jobs: int, limit: int | None = None) -> dict:
    import random
    samples: list[Sample] = []
    for name in datasets:
        rows = schema.read(parquet / f"{name}.parquet")
        if limit and len(rows) > limit:
            rows = random.Random(f"bench-limit-{name}").sample(rows, limit)
        samples += rows
    t0 = time.time()
    results, groups = score_samples(samples, jobs)
    summary = summarise(results, groups)
    seconds = time.time() - t0
    manifest = json.loads((parquet / "manifest.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps({**summary, "seconds": seconds, "limit": limit,
                                                  "manifest": manifest}, indent=2) + "\n", encoding="utf-8")
    (out / "report.md").write_text(report(summary, manifest, seconds), encoding="utf-8")
    return summary
