"""TAB, the Text Anonymization Benchmark of ECHR court decisions (docs/BENCHMARK.md, TAB). One sample per document.
Mentions with the same offsets are merged over the annotators: pos when any of them marked the mention DIRECT or
QUASI, neg when all said NO_MASK. Messages name the document and the mention, never the text."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from ..labels import LabelTable
from ..paths import BenchError
from ..schema import Sample, Span
from ..split import split_of

DATASET = "tab"
FILES = ("echr_train.json", "echr_dev.json", "echr_test.json")
_MASK = {"DIRECT", "QUASI"}


def _spans(doc: dict, table: LabelTable) -> list[Span]:
    text = doc["text"]
    merged: dict[tuple[int, int], tuple[str, bool]] = {}
    for annotation in doc["annotations"].values():
        for m in annotation["entity_mentions"]:
            a, b = m["start_offset"], m["end_offset"]
            if text[a:b] != m["span_text"]:
                raise BenchError(f"{DATASET}: {doc['doc_id']}: mention {m['entity_mention_id']} at {a}-{b} does "
                                 "not match its text")
            table.type_of(m["entity_type"])
            label, masked = merged.get((a, b), (m["entity_type"], False))
            merged[(a, b)] = (label, masked or m["identifier_type"] in _MASK)
    return [Span(a, b, label, table.type_of(label), "pos" if masked else "neg")
            for (a, b), (label, masked) in sorted(merged.items())]


def samples(root: Path, table: LabelTable) -> Iterator[Sample]:
    root = Path(root)
    present = [root / f for f in FILES if (root / f).is_file()]
    if not present:
        raise BenchError(f"{root}: none of {', '.join(FILES)}; is this a text-anonymization-benchmark checkout?")
    for path in present:
        for doc in json.loads(path.read_text(encoding="utf-8")):
            yield Sample(DATASET, doc["doc_id"], doc["doc_id"], "en", doc["text"], _spans(doc, table),
                         split_of(DATASET, doc["doc_id"]))
