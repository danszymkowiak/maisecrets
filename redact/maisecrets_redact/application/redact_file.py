"""One document through the pipeline, and a directory of them (TASK-34.5, TASK-34.6): extract, the rules, the models,
the vote, the review, the output. Files, formats and detectors come in through the ports (application/ports.py);
adapters/compose.py builds them."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..domain import fields, shape, text, vote
from ..domain.document import Detector, NoText
from ..domain.outputs import OUTPUT_SUFFIXES, output_name, outputs
from ..domain.placeholders import Placeholders
from ..domain.review_items import Item, items
from .ports import Ports


@dataclass
class Result:
    status: str                         # written, review, exists
    counts: dict = field(default_factory=dict)
    open_items: int = 0
    written: tuple[Path, ...] = ()


def run_file(ports: Ports, src: Path, target: Path, model_detectors: dict[str, Detector], interactive: bool,
             ask: Callable[[Item], str] | None = None, no_review: bool = False,
             drop_columns: frozenset[str] = frozenset(), names: Placeholders | None = None,
             vote_k: int | None = None, not_reviewed: tuple[str, ...] = ()) -> Result:
    doc = ports.extractor.extract(src, frozenset(drop_columns))
    labelled = fields.column_spans(doc) + fields.har_spans(doc) + fields.card_spans(doc)
    rule_spans = text.within_cells(doc, ports.rules(doc) + labelled)
    # the models run after the rules: they read the text with every rule hit replaced (user, 2026-10-12)
    masked = text.mask(doc, rule_spans)
    model_spans = {name: fields.plausible(doc, text.within_cells(doc, masked.back(d(masked.doc))))
                   for name, d in model_detectors.items()}
    doubted = [s for spans in model_spans.values() for s in fields.doubtful(doc, spans)]
    decision = vote.decide(doc, rule_spans, model_spans, k=vote_k, not_reviewed=not_reviewed, ask=doubted,
                           extra_review=shape.shape_spans(doc))
    redact = list(decision.redact)
    open_items = items(doc, decision, list(model_detectors))
    # a review file belongs to one version of the document: a changed document makes it stale, items or not
    decided = ports.reviews.read(target, doc)
    if open_items and no_review:
        redact += [i.span for i in open_items]
    elif open_items and interactive and ask is not None:
        redact += [i.span for i in open_items if ask(i) == "redact"]
    elif open_items:
        if any(decided.get(i.id) not in ("redact", "keep") for i in open_items):
            ports.reviews.write(target, doc, open_items, decided)
            return Result("review", open_items=sum(decided.get(i.id) is None for i in open_items))
        redact += [i.span for i in open_items if decided[i.id] == "redact"]
    names = names or Placeholders()
    out = [(target.with_name(p.name), content) for p, content in outputs(doc, target, redact, names.placeholder)]
    if any(ports.sink.exists(p) for p, _ in out):
        return Result("exists")          # an output is never overwritten, and a workbook is written whole or not at all
    for p, content in out:
        ports.sink.write(p, content)
    return Result("written", names.counts(), written=tuple(p for p, _ in out))


@dataclass
class DirSummary:
    written: int = 0
    review: int = 0           # files waiting on a review file
    skipped: int = 0          # unsupported types, symlinks out of the tree, files without text
    exists: int = 0           # outputs already there (never overwritten)
    counts: dict = field(default_factory=dict)


def run_dir(ports: Ports, src: Path, out: Path, model_detectors: dict[str, Detector], interactive: bool,
            recursive: bool = False, ask: Callable[[Item], str] | None = None, no_review: bool = False,
            drop_columns: frozenset[str] = frozenset(), log: Callable[[str], None] = lambda line: None,
            vote_k: int | None = None, not_reviewed: tuple[str, ...] = ()) -> DirSummary:
    """Every supported file of `src` into the mirrored tree `out`, one placeholder per value across the run. The
    source files are never written; `out` may be `src` itself (each output next to its file, the default of the
    command), but no other folder inside the source tree; a symlink out of the tree is skipped; an earlier output
    (`*.redacted.txt`, `*.redacted.csv`) is never an input."""
    tree = ports.tree
    if not tree.same(out, src) and tree.inside(out, src):
        raise ValueError(f"{out} is inside {src}: the output must not be written into the source tree")
    summary, names = DirSummary(), Placeholders()
    for path in tree.files(src, recursive):
        rel = path.relative_to(src)
        if tree.is_link(path) and not tree.inside(path, src):
            log(f"skip {rel}: a link that points outside the tree")
            summary.skipped += 1
            continue
        if path.name.endswith(OUTPUT_SUFFIXES):
            continue   # an output of an earlier run, in place: redacting it again would nest names
        if not ports.extractor.supports(path):
            log(f"skip {rel}: {path.suffix.lstrip('.') or 'no extension'} is not a supported type")
            summary.skipped += 1
            continue
        target = out / rel.parent / output_name(path)
        if ports.sink.exists(target):
            log(f"keep {rel}: {target.name} exists and is not overwritten")
            summary.exists += 1
            continue
        try:
            result = run_file(ports, path, target, model_detectors, interactive, ask, no_review, drop_columns, names,
                              vote_k, not_reviewed)
        except NoText as exc:
            log(f"skip {rel}: {exc}")
            summary.skipped += 1
            continue
        if result.status == "exists":
            log(f"keep {rel}: an output of it exists and is not overwritten")
            summary.exists += 1
        elif result.status == "review":
            log(f"review {rel}: {result.open_items} span(s) need a decision in {target.name}.review.json")
            summary.review += 1
        else:
            summary.written += 1
    summary.counts = names.counts()
    return summary
