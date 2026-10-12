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


@dataclass
class DirSummary:
    written: int = 0
    review: int = 0           # files waiting on a review file
    skipped: int = 0          # unsupported types, symlinks out of the tree, files without text
    exists: int = 0           # outputs already there (never overwritten)
    counts: dict = field(default_factory=dict)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def files_of(root: Path, recursive: bool) -> list[Path]:
    """The files of a tree in a fixed order (placeholders are numbered in it); symlinked folders are not entered."""
    import os
    if not recursive:
        return sorted(p for p in root.iterdir() if p.is_file() or p.is_symlink())
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        out += [Path(dirpath) / f for f in sorted(filenames)]
    return out


def run_dir(src: Path, out: Path, model_detectors: dict[str, Detector], regions: tuple[str, ...] | None,
            interactive: bool, recursive: bool = False, ask: Callable[[review.Item], str] | None = None,
            no_review: bool = False, drop_columns: frozenset[str] = frozenset(),
            log: Callable[[str], None] = lambda line: None) -> DirSummary:
    """Every supported file of `src` into the mirrored tree `out`, one placeholder per value across the run. The
    source is never written; an output inside the source tree is refused; a symlink out of the tree is skipped."""
    if _inside(out, src):
        raise ValueError(f"{out} is inside {src}: the output must not be written into the source tree")
    summary, names = DirSummary(), rules.Placeholders()
    for path in files_of(src, recursive):
        rel = path.relative_to(src)
        if path.is_symlink() and not _inside(path, src):
            log(f"skip {rel}: a link that points outside the tree")
            summary.skipped += 1
            continue
        if path.suffix.lower() not in extract.SUPPORTED:
            log(f"skip {rel}: {path.suffix.lstrip('.') or 'no extension'} is not a supported type")
            summary.skipped += 1
            continue
        target = out / rel.parent / (path.name + ".redacted.txt")
        if target.exists():
            log(f"keep {rel}: {target.name} exists and is not overwritten")
            summary.exists += 1
            continue
        try:
            result = run_file(path, target, model_detectors, regions, interactive, ask, no_review, drop_columns, names)
        except extract.NoText as exc:
            log(f"skip {rel}: {exc}")
            summary.skipped += 1
            continue
        if result.status == "review":
            log(f"review {rel}: {result.open_items} span(s) need a decision in {target.name}.review.json")
            summary.review += 1
        else:
            summary.written += 1
    summary.counts = names.counts()
    return summary
