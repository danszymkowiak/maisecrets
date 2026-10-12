"""The tool on the bench datasets (TASK-34.8): which personal values the rules alone, each model, the rules with each
model and the vote hide, which spans they redact that touch no gold value, and the time per document on CPU.

    uv run --project redact --with pyarrow python -m maisecrets_redact.measure [--per-dataset 150] [--models a,b]

Reads the bench parquet (bench/setup.py writes it; docs/BENCHMARK.md) and writes, under <bench data>/redact/<time>/,
spans.jsonl (offsets and types per detector, never text) and report.md. ai4privacy is never read (its licence keeps
it local to the plugin's bench). Developer tool: nothing of it ships.

A gold value counts as hidden when the redacted spans together cover at least 80 % of its characters: the rest of
it reaching the model is a partial leak, and a looser rule would count a first name redacted out of a full name as a
find. Uncertain gold counts neither way. A redacted span that touches no positive or uncertain gold span (of any
label) is a false positive: the datasets label companies, dates and cities as positive too, so hiding one is not
counted against a model that hides more than the scored types, while a span on a negative one (findocs' amounts,
dates and references) or on unlabelled text is.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from . import pipeline
from .pipeline import Document, Span

DATASETS = ("findocs", "gretel", "nemotron", "mendeley")
COVER = 0.8
# dataset labels (lower case) -> the types scored here; the plugin's own bench scores the rest
GOLD_TYPES = {
    "name": "NAME", "first_name": "NAME", "last_name": "NAME",
    "street_address": "ADDRESS", "address": "ADDRESS",
    "email": "EMAIL", "phone": "PHONE", "phone_number": "PHONE", "fax_number": "PHONE",
    "date_of_birth": "DOB", "dob": "DOB",
    "iban": "ACCOUNT", "bban": "ACCOUNT", "account": "ACCOUNT", "account_number": "ACCOUNT",
    "ahv": "NATIONAL_ID", "ssn": "NATIONAL_ID", "passport_number": "PASSPORT",
}


def gold_type(dataset: str, label: str) -> str | None:
    return GOLD_TYPES.get(label.lower())


def _covered(a: int, b: int, spans: list[Span]) -> int:
    marks = bytearray(b - a)
    for s in spans:
        for i in range(max(a, s.start), min(b, s.end)):
            marks[i - a] = 1
    return sum(marks)


class Score:
    def __init__(self) -> None:
        self.found: Counter = Counter()       # (dataset, gold type)
        self.total: Counter = Counter()
        self.false_pos: Counter = Counter()   # (dataset, detected type)
        self.words: Counter = Counter()       # dataset -> words scored

    def add(self, dataset: str, gold: list[dict], spans: list[Span], words: int = 0) -> None:
        self.words[dataset] += words
        for g in gold:
            t = gold_type(dataset, g["label"])
            if t is None or g["gold"] != "pos":
                continue
            self.total[(dataset, t)] += 1
            if _covered(g["start"], g["end"], spans) >= COVER * (g["end"] - g["start"]):
                self.found[(dataset, t)] += 1
        for s in spans:
            if not any(s.start < g["end"] and g["start"] < s.end for g in gold if g["gold"] != "neg"):
                self.false_pos[(dataset, s.type)] += 1


def vote(text: str, rule_spans: list[Span], per_model: dict[str, list[Span]], k: int | None = None,
         not_reviewed: tuple[str, ...] = ()) -> tuple[list[Span], list[Span]]:
    """What the tool redacts without asking, and what it sends to a person (review.decide, the tool's own vote)."""
    from .review import decide
    d = decide(Document("bench", text), rule_spans, per_model, k=k, not_reviewed=not_reviewed)
    return list(d.redact), list(d.review)


# ------------------------------------------------------------------------------------------------- the run --
def _bench_data() -> Path:
    raw = os.environ.get("MAISECRETS_BENCH_DATA")
    return Path(raw).expanduser().resolve() if raw else Path.home() / ".cache" / "maisecrets-bench"


def _samples(data: Path, name: str, n: int) -> list[dict]:
    import pyarrow.parquet as pq
    rows = pq.read_table(data / "parquet" / f"{name}.parquet",
                         columns=["sample_id", "text", "spans", "split"]).to_pylist()
    rows = [r for r in rows if r["split"] == "dev"
            and any(gold_type(name, s["label"]) and s["gold"] == "pos" for s in r["spans"])]
    rows.sort(key=lambda r: r["sample_id"])
    return random.Random(34).sample(rows, min(n, len(rows)))


def _detect(data: Path, out: Path, per_dataset: int, model_ids: list[str]) -> None:
    from . import models, rules
    detectors = {"rules": rules.detector(regions=("ch", "us"))}
    for mid, det in zip(model_ids, models.load(model_ids)):
        detectors[mid] = det
    with (out / "spans.jsonl").open("w", encoding="utf-8") as f:
        for name in DATASETS:
            for r in _samples(data, name, per_dataset):
                doc = Document(r["sample_id"], r["text"])
                masked = None
                for det_name, det in detectors.items():   # the rules first: the models read the masked text, as in app
                    t = time.perf_counter()
                    if det_name == "rules":
                        spans = det(doc)
                        masked = pipeline.mask(doc, spans)
                    else:
                        spans = masked.back(det(masked.doc))
                    f.write(json.dumps({"dataset": name, "sample_id": r["sample_id"], "detector": det_name,
                                        "seconds": round(time.perf_counter() - t, 4),
                                        "spans": [[s.start, s.end, s.type, round(s.score, 3)] for s in spans]})
                            + "\n")
            print(f"measure: {name} done", file=sys.stderr, flush=True)


def report(data: Path, out: Path, defaults: tuple[str, ...]) -> str:
    by_sample: dict[tuple[str, str], dict[str, list[Span]]] = {}
    seconds: Counter = Counter()
    docs: Counter = Counter()
    for line in (out / "spans.jsonl").read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        spans = [Span(a, b, t, rec["detector"], sc) for a, b, t, sc in rec["spans"]]
        by_sample.setdefault((rec["dataset"], rec["sample_id"]), {})[rec["detector"]] = spans
        seconds[rec["detector"]] += rec["seconds"]
        docs[rec["detector"]] += 1
    detectors = sorted({d for v in by_sample.values() for d in v})
    model_ids = [d for d in detectors if d != "rules"]
    configs: dict[str, Score] = {"rules": Score()}
    for m in model_ids:
        configs[f"{m} alone"] = Score()
        configs[f"rules + {m}"] = Score()
    voters = [m for m in defaults if m in model_ids]
    if voters:
        configs["vote, no review"] = Score()
        configs["vote, review all yes"] = Score()
    import pyarrow.parquet as pq
    for name in DATASETS:
        rows = {r["sample_id"]: r for r in pq.read_table(data / "parquet" / f"{name}.parquet",
                                                         columns=["sample_id", "text", "spans"]).to_pylist()}
        for (ds, sid), per in by_sample.items():
            if ds != name:
                continue
            r = rows[sid]
            words = len(r["text"].split())
            configs["rules"].add(ds, r["spans"], per["rules"], words)
            for m in model_ids:
                configs[f"{m} alone"].add(ds, r["spans"], per[m], words)
                configs[f"rules + {m}"].add(ds, r["spans"], per["rules"] + per[m], words)
            if voters:
                from . import models
                redact, review = vote(r["text"], per["rules"], {m: per[m] for m in voters}, models.VOTE_K,
                                      tuple(m for m in models.NOT_REVIEWED if m in voters))
                configs["vote, no review"].add(ds, r["spans"], redact, words)
                configs["vote, review all yes"].add(ds, r["spans"], redact + review, words)
    return _render(configs, seconds, docs, voters)


def _render(configs: dict[str, Score], seconds: Counter, docs: Counter, voters: list[str]) -> str:
    types = sorted({t for s in configs.values() for (_, t) in s.total})
    lines = ["# redact on the bench datasets (TASK-34.8)", "",
             f"A value counts as hidden when redacted spans cover {COVER:.0%} of its characters. False positives: "
             "redacted spans touching no positive or uncertain gold span, per 1,000 words. "
             f"Vote: {', '.join(voters) or '-'} (review.decide).", "",
             "## Recall per type (all datasets)", "",
             "| configuration | " + " | ".join(types) + " | FP / 1k words |",
             "|---|" + "---|" * (len(types) + 1)]
    for name, s in configs.items():
        cells = []
        for t in types:
            f = sum(v for (d, tt), v in s.found.items() if tt == t)
            n = sum(v for (d, tt), v in s.total.items() if tt == t)
            cells.append(f"{f / n:.1%} ({f}/{n})" if n else "-")
        fp = sum(s.false_pos.values()) * 1000 / max(1, sum(s.words.values()))
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {fp:.1f} |")
    lines += ["", "## Recall and false positives per dataset", "",
              "| configuration | dataset | recall (all scored types) | FP / 1k words |", "|---|---|---|---|"]
    for name, s in configs.items():
        for ds in DATASETS:
            f = sum(v for (d, _), v in s.found.items() if d == ds)
            n = sum(v for (d, _), v in s.total.items() if d == ds)
            if n:
                fp = sum(v for (d, _), v in s.false_pos.items() if d == ds) * 1000 / max(1, s.words[ds])
                lines.append(f"| {name} | {ds} | {f / n:.1%} ({f}/{n}) | {fp:.1f} |")
    lines += ["", "## Time per document (CPU)", "", "| detector | seconds per document |", "|---|---|"]
    for d in sorted(seconds):
        lines.append(f"| {d} | {seconds[d] / docs[d]:.3f} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-dataset", type=int, default=150)
    ap.add_argument("--models", help="comma-separated model ids (default: every permissive model)")
    ap.add_argument("--report-only", type=Path, metavar="DIR", help="score an earlier run's spans.jsonl again")
    args = ap.parse_args(argv)
    os.environ["MAISECRETS_HOME"] = tempfile.mkdtemp(prefix="redact-measure-home-")   # never the real plugin home
    from . import models
    data = _bench_data()
    if args.report_only:
        out = args.report_only
    else:
        ids = ([m.strip() for m in args.models.split(",") if m.strip()] if args.models
               else [m for m, info in models.MODELS.items() if info.licence in models.PERMISSIVE])
        out = data / "redact" / time.strftime("%Y%m%d-%H%M%S")
        out.mkdir(parents=True, exist_ok=True)
        _detect(data, out, args.per_dataset, ids)
    text = report(data, out, models.DEFAULTS)
    (out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"report: {out / 'report.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
