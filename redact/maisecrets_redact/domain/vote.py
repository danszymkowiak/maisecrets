"""The vote (TASK-34.5, TASK-34.8): rule hits redact; overlapping model spans form a group, redacted when enough
models hold a span in it, and sent to a person otherwise."""
from __future__ import annotations

from collections import Counter

from .document import Decision, Document, Span
from .text import overlapping


def decide(doc: Document, rule_spans: list[Span], model_spans: dict[str, list[Span]], k: int | None = None,
           not_reviewed: tuple[str, ...] = (), ask: list[Span] | tuple[Span, ...] = (),
           extra_review: list[Span] | tuple[Span, ...] = ()) -> Decision:
    """k: how many models must hold a span in a group to redact it (None: every configured model, of one type).
    not_reviewed: models whose lone spans are dropped instead of asked about (TASK-34.8: privacy-filter's many lone
    spans were most of the review questions). ask: spans whose group a person decides even when the models agree
    (doubtful, TASK-57). extra_review: spans a person decides that no vote redacts (the password shape,
    TASK-55), asked about unless a rule or another span already covers them."""
    rules = sorted(rule_spans, key=lambda s: s.start)
    on_rule, doubted = overlapping(rules), overlapping(ask)
    loose = sorted((s for spans in model_spans.values() for s in spans if not on_rule(s.start, s.end)),
                   key=lambda s: (s.start, -s.end))
    redact, review = list(rules), []
    group: list[Span] = []
    group_end = 0

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
        if agreed and not doubted(start, end):
            redact.append(span)
        elif not sources <= set(not_reviewed):
            review.append(span)

    for s in loose:
        if group and s.start >= group_end:
            close(group)
            group = []
        group.append(s)
        group_end = max(group_end, s.end) if len(group) > 1 else s.end
    close(group)
    covered = overlapping([*redact, *review])
    review += [s for s in sorted(extra_review, key=lambda s: s.start) if not covered(s.start, s.end)]
    return Decision(tuple(sorted(redact, key=lambda s: s.start)), tuple(sorted(review, key=lambda s: s.start)))
