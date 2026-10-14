"""Gretel synthetic_pii_finance_multilingual (docs/BENCHMARK.md): one sample per generated finance document. Its
pii_spans are the gold; unlabelled text is negative. A span whose offsets fall outside the text or are empty is
dropped and counted (the dataset has a few hundred); every other problem stops the setup.

A record below quality 90 (Gretel's own quality_score, 80 to 97) is dropped and counted, as a study that used the
dataset did (TASK-11.33). The rigidly structured formats that study dropped (CSV, EDI, SWIFT, FIX, BAI, XBRL, FpML,
MT940) stay, tagged format:structured, because bank and tax exports look like them; the report scores them apart."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Iterator

from ...domain.labels import LabelTable
from ...domain.bench_error import BenchError
from ...domain.samples import Sample, Span
from ...domain.split import split_of

DATASET = "gretel"
HF_ID = "gretelai/synthetic_pii_finance_multilingual"
MIN_QUALITY = 90
STRUCTURED = {"CSV", "EDI", "SWIFT Message", "FIX Protocol", "BAI Format", "XBRL", "FpML", "MT940"}
REVISION = "q90-format-tags"    # part of the version: a change here builds the parquet again
# the dataset's language names; it writes "France" for French
LANGUAGES = {"English": "en", "German": "de", "France": "fr", "French": "fr", "Spanish": "es", "Italian": "it",
             "Dutch": "nl", "Swedish": "sv"}


@dataclass
class Stats:
    dropped: int = 0
    low_quality: int = 0


def samples(records: Iterable[dict], table: LabelTable, stats: Stats) -> Iterator[Sample]:
    for r in records:
        sid = f"{r['_split']}:{r['index']}"
        if r["quality_score"] < MIN_QUALITY:
            stats.low_quality += 1
            continue
        try:
            language = LANGUAGES[r["language"]]
        except KeyError:
            raise BenchError(f"{DATASET}: {sid}: language {r['language']!r} has no code; add it to LANGUAGES") from None
        text = r["generated_text"]
        spans = []
        for m in json.loads(r["pii_spans"]):
            t = table.type_of(m["label"])
            if not 0 <= m["start"] < m["end"] <= len(text):
                stats.dropped += 1
                continue
            spans.append(Span(m["start"], m["end"], m["label"], t, "pos"))
        spans.sort(key=lambda s: (s.start, s.end))
        fmt = "structured" if r["document_type"] in STRUCTURED else "unstructured"
        yield Sample(DATASET, sid, sid, language, text, spans, split_of(DATASET, sid), [f"format:{fmt}"])


def records(cache_dir: str) -> Iterator[dict]:
    """Every record of the train and test splits, downloaded once into the bench's cache."""
    from datasets import load_dataset
    ds = load_dataset(HF_ID, cache_dir=cache_dir)
    for split in ds:
        for r in ds[split]:
            yield {**r, "_split": split}
