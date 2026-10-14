"""A review question (TASK-34.5): the span, where it is, and the words around it with every value masked."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .document import Decision, Document, Span


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


def digest(text: str) -> str:
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
