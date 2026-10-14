"""The review file (TASK-34.5): the open items with their values masked, and the decisions a person writes into it."""
from __future__ import annotations

import json
from pathlib import Path

from ..domain.document import Document
from ..domain.review_items import Item, digest


class StaleReview(ValueError):
    """The document changed after its review file was written."""


def write_file(path: Path, doc: Document, open_items: list[Item], decisions: dict[str, object]) -> None:
    data = {"about": "Review of the spans the local models disagree on (redact, TASK-34.5). Set each decision to "
                     "\"redact\" or \"keep\", then run redact again. The values are masked here; the position says "
                     "where to look in the source.",
            "document": doc.path, "text_sha256": digest(doc.text),
            "items": [{"id": i.id, "where": i.where, "type": i.span.type, "context": i.context,
                       "models_agreed": list(i.agreed), "models_missing": list(i.missing),
                       "decision": decisions.get(i.id)} for i in open_items]}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_file(path: Path, doc: Document) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("text_sha256") != digest(doc.text):
        raise StaleReview(f"{doc.path} changed after {path.name} was written; delete it to review again")
    return {it["id"]: it.get("decision") for it in data.get("items", [])}


def review_path(target: Path) -> Path:
    return target.with_name(target.name + ".review.json")


class ReviewFile:
    """The ReviewStore port: <output>.review.json next to the output."""

    def read(self, target: Path, doc: Document) -> dict[str, object]:
        path = review_path(target)
        return read_file(path, doc) if path.exists() else {}

    def write(self, target: Path, doc: Document, items: list[Item], decided: dict[str, object]) -> None:
        write_file(review_path(target), doc, items, decided)
