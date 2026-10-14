"""The vote and the review gate (TASK-34.5). decide() is pure: rule hits redact; overlapping model spans form a group,
redacted when every configured model holds a span of one type in it, and sent to a person otherwise. The review file
holds the open items with the surrounding words masked (every other redacted value shows as its type, the item itself
as [TYPE?]), never a value; a second run applies the decisions written into it."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .pipeline import Decision, Document, Span


class StaleReview(ValueError):
    """The document changed after its review file was written."""


def _overlaps(a: Span, b: Span) -> bool:
    return a.start < b.end and b.start < a.end


def decide(doc: Document, rule_spans: list[Span], model_spans: dict[str, list[Span]], k: int | None = None,
           not_reviewed: tuple[str, ...] = (), ask: list[Span] | tuple[Span, ...] = ()) -> Decision:
    """k: how many models must hold a span in a group to redact it (None: every configured model, of one type).
    not_reviewed: models whose lone spans are dropped instead of asked about (TASK-34.8: privacy-filter's many lone
    spans were most of the review questions). ask: spans whose group a person decides even when the models agree
    (pipeline.doubtful, TASK-57)."""
    rules = sorted(rule_spans, key=lambda s: s.start)
    loose = sorted((s for spans in model_spans.values() for s in spans if not any(_overlaps(s, r) for r in rules)),
                   key=lambda s: (s.start, -s.end))
    redact, review = list(rules), []
    group: list[Span] = []

    def close(group: list[Span]) -> None:
        if not group:
            return
        start, end = min(s.start for s in group), max(s.end for s in group)
        types_by_model = {name: {s.type for s in group if s.source == name} for name in model_spans}
        common = set.intersection(*types_by_model.values()) if types_by_model else set()
        kind = sorted(common)[0] if common else Counter(s.type for s in group).most_common(1)[0][0]
        sources = {s.source for s in group}
        span = Span(start, end, kind, "+".join(sorted(sources)), min(s.score for s in group))
        agreed = bool(common) if k is None else len(sources) >= min(k, len(model_spans))
        doubted = any(a.start < end and start < a.end for a in ask)
        if agreed and not doubted:
            redact.append(span)
        elif not sources <= set(not_reviewed):
            review.append(span)

    for s in loose:
        if group and s.start >= max(g.end for g in group):
            close(group)
            group = []
        group.append(s)
    close(group)
    return Decision(tuple(sorted(redact, key=lambda s: s.start)), tuple(sorted(review, key=lambda s: s.start)))


@dataclass(frozen=True)
class Item:
    id: str
    span: Span
    where: str
    context: str
    agreed: tuple[str, ...]
    missing: tuple[str, ...]


def _where(doc: Document, span: Span) -> str:
    return next((p.where for p in doc.positions if p.start <= span.start < p.end), "")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def items(doc: Document, decision: Decision, models: list[str], width: int = 40) -> list[Item]:
    out = []
    for n, s in enumerate(decision.review, 1):
        a, b = max(0, s.start - width), min(len(doc.text), s.end + width)
        masked, at = [], a
        for other in sorted([*decision.redact, *decision.review], key=lambda x: x.start):
            if other.end <= a or other.start >= b:
                continue
            masked += [doc.text[at:max(at, other.start)], f"[{other.type}?]" if other is s else f"[{other.type}]"]
            at = max(at, other.end)
        masked.append(doc.text[at:b])
        agreed = tuple(sorted(set(s.source.split("+"))))
        out.append(Item(f"{n}:{s.start}-{s.end}", s, _where(doc, s), " ".join("".join(masked).split()), agreed,
                        tuple(m for m in models if m not in agreed)))
    return out


def write_file(path: Path, doc: Document, open_items: list[Item], decisions: dict[str, object]) -> None:
    data = {"about": "Review of the spans the local models disagree on (redact, TASK-34.5). Set each decision to "
                     "\"redact\" or \"keep\", then run redact again. The values are masked here; the position says "
                     "where to look in the source.",
            "document": doc.path, "text_sha256": _digest(doc.text),
            "items": [{"id": i.id, "where": i.where, "type": i.span.type, "context": i.context,
                       "models_agreed": list(i.agreed), "models_missing": list(i.missing),
                       "decision": decisions.get(i.id)} for i in open_items]}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_file(path: Path, doc: Document) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("text_sha256") != _digest(doc.text):
        raise StaleReview(f"{doc.path} changed after {path.name} was written; delete it to review again")
    return {it["id"]: it.get("decision") for it in data.get("items", [])}
