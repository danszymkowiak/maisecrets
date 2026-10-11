"""ai4privacy pii-masking-300k (docs/BENCHMARK.md). LOCAL AND OPT-IN: its licence allows academic and non-commercial
use only and needs a written licence from AI4Privacy for derivative works. The user measures with it on their own
machine; nothing derived from it goes upstream, and the plugin's owner must get AI4Privacy's permission first
(licensing@ai4privacy.com). One sample per record; privacy_mask spans are the gold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from ..labels import LabelTable
from ..paths import BenchError
from ..schema import Sample, Span
from ..split import split_of

DATASET = "ai4privacy"
HF_ID = "ai4privacy/pii-masking-300k"
LICENCE_NOTE = ("ai4privacy: academic and non-commercial use only (AI4Privacy licence). Local measurement; leave it "
                "out of anything sent upstream. The plugin's owner needs AI4Privacy's permission first.")
LANGUAGES = {"English": "en", "Dutch": "nl", "French": "fr", "German": "de", "Italian": "it", "Spanish": "es"}


@dataclass
class Stats:
    dropped: int = 0


def samples(records: Iterable[dict], table: LabelTable, stats: Stats) -> Iterator[Sample]:
    for r in records:
        sid = f"{r['set']}:{r['id']}"
        try:
            language = LANGUAGES[r["language"]]
        except KeyError:
            raise BenchError(f"{DATASET}: {sid}: language {r['language']!r} has no code; add it to LANGUAGES") from None
        text = r["source_text"]
        spans = []
        for m in r["privacy_mask"]:
            t = table.type_of(m["label"])
            if not (0 <= m["start"] < m["end"] <= len(text)) or text[m["start"]:m["end"]] != m["value"]:
                stats.dropped += 1
                continue
            spans.append(Span(m["start"], m["end"], m["label"], t, "pos"))
        spans.sort(key=lambda s: (s.start, s.end))
        yield Sample(DATASET, sid, sid, language, text, spans, split_of(DATASET, sid))


def records(cache_dir: str) -> Iterator[dict]:
    from datasets import load_dataset
    ds = load_dataset(HF_ID, cache_dir=cache_dir)
    for split in ds:
        yield from ds[split]
