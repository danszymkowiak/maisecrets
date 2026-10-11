"""Gretel synthetic_pii_finance_multilingual (docs/BENCHMARK.md): one sample per generated finance document. Its
pii_spans are the gold; unlabelled text is negative. A span whose offsets fall outside the text or are empty is
dropped and counted (the dataset has a few hundred); every other problem stops the setup."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Iterator

from ..labels import LabelTable
from ..paths import BenchError
from ..schema import Sample, Span
from ..split import split_of

DATASET = "gretel"
HF_ID = "gretelai/synthetic_pii_finance_multilingual"
# the dataset's language names; it writes "France" for French
LANGUAGES = {"English": "en", "German": "de", "France": "fr", "French": "fr", "Spanish": "es", "Italian": "it",
             "Dutch": "nl", "Swedish": "sv"}


@dataclass
class Stats:
    dropped: int = 0


def samples(records: Iterable[dict], table: LabelTable, stats: Stats) -> Iterator[Sample]:
    for r in records:
        sid = f"{r['_split']}:{r['index']}"
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
        yield Sample(DATASET, sid, sid, language, text, spans, split_of(DATASET, sid))


def records(cache_dir: str) -> Iterator[dict]:
    """Every record of the train and test splits, downloaded once into the bench's cache."""
    from datasets import load_dataset
    ds = load_dataset(HF_ID, cache_dir=cache_dir)
    for split in ds:
        for r in ds[split]:
            yield {**r, "_split": split}
