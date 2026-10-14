"""Reviewed gold exceptions (TASK-30): bench/gold_exceptions.json (read by adapters/files.py) lists the cases no
validity rule of validgold.py
catches. Each entry names its place (dataset, sample id, start, end, label) and a sha256 of the span's text, so a
changed dataset shows a stale entry instead of moving it to another span; the file never holds a value.

    {"entries": [{"dataset": "gretel", "sample_id": "test:123", "start": 10, "end": 19, "label": "phone_number",
                  "text_sha256": "<first 16 hex>", "verdict": "negative", "rationale": "a product number"}]}

verdict: negative (the label is wrong, the text is no personal data: a detection is a false alarm), uncertain
(PII-shaped but invalid: neither a miss nor a false alarm), drop (the whole record is broken)."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import Counter
from .bench_error import BenchError
from .samples import Sample


FIELDS = ("dataset", "sample_id", "start", "end", "label", "text_sha256", "verdict", "rationale")


VERDICTS = {"negative": "neg", "uncertain": "uncertain", "drop": None}


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def check(data: dict, name: str = "gold_exceptions.json") -> list[dict]:
    """The entries of the parsed file, each checked; `name` is the file's name in the error messages."""
    entries = data.get("entries", [])
    for n, e in enumerate(entries, 1):
        missing = [f for f in FIELDS if f not in e]
        if missing:
            raise BenchError(f"{name}, entry {n}: missing {', '.join(missing)}")
        if e["verdict"] not in VERDICTS:
            raise BenchError(f"{name}, entry {n}: verdict {e['verdict']!r} is not one of {', '.join(VERDICTS)}")
        if not str(e["rationale"]).strip():
            raise BenchError(f"{name}, entry {n}: an exception needs its rationale")
    return entries


def digest(entries: list[dict], dataset: str) -> str:
    """A version of one dataset's entries: a change to them builds that dataset again."""
    mine = sorted(json.dumps(e, sort_keys=True) for e in entries if e["dataset"] == dataset)
    return hashlib.sha256("\n".join(mine).encode("utf-8")).hexdigest()[:12]


def apply(samples: list[Sample], entries: list[dict]) -> tuple[list[Sample], dict]:
    """The samples with the entries of their datasets applied, and a count per verdict. A stale entry stops."""
    names = {s.dataset for s in samples}
    todo = {}
    for e in entries:
        if e["dataset"] in names:
            todo.setdefault((e["dataset"], e["sample_id"]), []).append(e)
    counts: Counter = Counter()
    out = []
    for s in samples:
        mine = todo.pop((s.dataset, s.sample_id), [])
        if not mine:
            out.append(s)
            continue
        spans = list(s.spans)
        drop = False
        for e in mine:
            place = (e["start"], e["end"], e["label"])
            i = next((i for i, sp in enumerate(spans) if (sp.start, sp.end, sp.label) == place
                      and digest_text(s.text[sp.start:sp.end]) == e["text_sha256"]), None)
            if i is None:
                raise BenchError(f"gold exception stale: {e['dataset']}/{e['sample_id']} {e['start']}-{e['end']} "
                                 f"{e['label']} no longer matches its sample")
            counts[e["verdict"]] += 1
            if e["verdict"] == "drop":
                drop = True
            else:
                spans[i] = dataclasses.replace(spans[i], gold=VERDICTS[e["verdict"]])
        if not drop:
            out.append(dataclasses.replace(s, spans=spans))
    if todo:
        (ds, sid), (e, *_) = next(iter(todo.items())), next(iter(todo.values()))
        raise BenchError(f"gold exception stale: {ds}/{sid} {e['start']}-{e['end']} {e['label']}: no such sample")
    return out, dict(counts)
