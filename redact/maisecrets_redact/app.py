"""One document through the pipeline (TASK-34.5): extract, the rules, the models, the vote, the review, the output.
The command (cli.py) parses arguments and builds the detectors; run_file is driven by tests with fake models."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import extract, pipeline, review, rules
from .pipeline import Detector


@dataclass
class Result:
    status: str                         # written, review
    counts: dict = field(default_factory=dict)
    open_items: int = 0


def run_file(src: Path, target: Path, model_detectors: dict[str, Detector], regions: tuple[str, ...] | None,
             interactive: bool, ask: Callable[[review.Item], str] | None = None, no_review: bool = False,
             drop_columns: frozenset[str] = frozenset(), names: rules.Placeholders | None = None) -> Result:
    doc = extract.extract(src, drop_columns=set(drop_columns))
    rule_spans = rules.detector(regions=regions)(doc)
    model_spans = {name: d(doc) for name, d in model_detectors.items()}
    decision = review.decide(doc, rule_spans, model_spans)
    redact = list(decision.redact)
    open_items = review.items(doc, decision, list(model_detectors))
    review_path = target.with_name(target.name + ".review.json")
    # a review file belongs to one version of the document: a changed document makes it stale, items or not
    decided = review.read_file(review_path, doc) if review_path.exists() else {}
    if open_items and no_review:
        redact += [i.span for i in open_items]
    elif open_items and interactive and ask is not None:
        redact += [i.span for i in open_items if ask(i) == "redact"]
    elif open_items:
        if any(decided.get(i.id) not in ("redact", "keep") for i in open_items):
            review.write_file(review_path, doc, open_items, decided)
            return Result("review", open_items=sum(decided.get(i.id) is None for i in open_items))
        redact += [i.span for i in open_items if decided[i.id] == "redact"]
    names = names or rules.Placeholders()
    text = pipeline.render(doc, redact, names.placeholder)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return Result("written", names.counts())
