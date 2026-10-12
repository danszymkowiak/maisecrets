"""ai4privacy pii-masking-300k (docs/BENCHMARK.md). LOCAL AND OPT-IN: its licence allows academic and non-commercial
use only and needs a written licence from AI4Privacy for derivative works. The user measures with it on their own
machine; nothing derived from it goes upstream, and the plugin's owner must get AI4Privacy's permission first
(licensing@ai4privacy.com). One sample per record; privacy_mask spans are the gold."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator

from ..labels import LabelTable
from ..paths import BenchError
from ..schema import OUT_OF_SCOPE, Sample, Span
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
        lead = continuation_lead(str(r["id"]), text, spans)
        if lead:
            spans.append(lead)
        spans.sort(key=lambda s: (s.start, s.end))
        yield Sample(DATASET, sid, sid, language, text, spans, split_of(DATASET, sid))


REVISION = "cont1"      # cont1: a continuation record's first token is uncertain (TASK-33)
_CONTINUATION = re.compile(r"\d+[B-Z]")


def continuation_lead(rid: str, text: str, spans: list) -> Span | None:
    """ai4privacy cut a long text into records ...A, ...B, ...C; a continuation starts in the middle of a value its
    chunking left unlabelled (about 1,300 dev false alarms, TASK-11.17 family C). Its first token is uncertain gold:
    a detection there counts neither as found nor as a false alarm (TASK-33, the user's decision of 2026-10-12)."""
    if not _CONTINUATION.fullmatch(rid) or any(s.start == 0 for s in spans):
        return None
    m = re.match(r"\S{1,64}", text)
    return Span(0, m.end(), "continuation-start", OUT_OF_SCOPE, "uncertain") if m else None


def records(cache_dir: str) -> Iterator[dict]:
    from datasets import load_dataset
    ds = load_dataset(HF_ID, cache_dir=cache_dir)
    for split in ds:
        yield from ds[split]
