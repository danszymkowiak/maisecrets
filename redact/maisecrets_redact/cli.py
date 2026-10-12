"""The redact command: parses arguments, builds the detectors and asks at a terminal (docs/REDACT.md). The work is in
app.run_file. Nothing it prints holds a value: summaries are counts, a review shows the position and the masked
context, because the command may run where its output reaches a language model."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, extract, review


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="redact", description="Extract the text of a document (PDF, CSV, Excel, text) and redact personal data "
                                   "and secrets in it, before the text goes to a language model. See docs/REDACT.md.")
    ap.add_argument("path", metavar="PATH", help="a file, or a directory to redact every supported file in")
    ap.add_argument("--out", metavar="DIR",
                    help="where the redacted text goes (default: next to a file; <dir>.redacted for a directory)")
    ap.add_argument("--recursive", "-r", action="store_true", help="for a directory: its subfolders too")
    ap.add_argument("--regions", metavar="LIST",
                    help="country rules, comma-separated (for example ch,de); default: your maisecrets config")
    ap.add_argument("--drop-column", metavar="HEADER", action="append", default=[],
                    help="leave a CSV or Excel column out by its header (repeatable)")
    ap.add_argument("--rules-only", action="store_true", help="the plugin's rules alone, no local models")
    ap.add_argument("--models", metavar="LIST", help="model ids, comma-separated (default: the permissive defaults)")
    ap.add_argument("--accept-model-terms", metavar="MODEL", action="append", default=[],
                    help="use a model with restrictive terms after reading them (repeatable)")
    ap.add_argument("--no-review", "--accept-all", dest="no_review", action="store_true",
                    help="redact every span the models disagree on instead of asking")
    ap.add_argument("--version", action="version", version=f"redact {__version__}")
    return ap


def _ask(item: review.Item) -> str:
    print(f"\n{item.where or 'text'}: {item.span.type}? found by {', '.join(item.agreed)}, "
          f"not by {', '.join(item.missing) or '-'}\n  {item.context}", file=sys.stderr)
    while True:
        answer = input("  redact it? [y]es / [n]o: ").strip().lower()
        if answer in ("y", "yes"):
            return "redact"
        if answer in ("n", "no"):
            return "keep"


def _model_detectors(args) -> dict:
    if args.rules_only:
        return {}
    from . import models
    reason = models.unavailable_reason()
    if reason:
        print(f"redact: {reason}", file=sys.stderr)
        return {}
    ids = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else list(models.DEFAULTS)
    return dict(zip(ids, models.load(ids, tuple(args.accept_model_terms))))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    from . import app, paths
    try:
        paths.import_detector()      # the rules first: a missing checkout fails before minutes of model loading
    except RuntimeError as exc:
        print(f"redact: {exc}; nothing is written", file=sys.stderr)
        return 2
    src = Path(args.path)
    if src.is_dir():
        return _run_dir(args, src)
    if not src.is_file():
        print(f"redact: {src}: no such file or directory", file=sys.stderr)
        return 2
    target = Path(args.out) / (src.name + ".redacted.txt") if args.out else src.with_name(src.name + ".redacted.txt")
    if target.exists():
        print(f"redact: {target} exists; nothing is overwritten", file=sys.stderr)
        return 1
    regions = tuple(r.strip().lower() for r in args.regions.split(",") if r.strip()) if args.regions else None
    try:
        detectors = _model_detectors(args)
        result = app.run_file(src, target, detectors, regions, interactive=sys.stdin.isatty(), ask=_ask,
                              no_review=args.no_review, drop_columns=frozenset(args.drop_column))
    except RuntimeError as exc:      # no maisecrets checkout to take the rules from
        print(f"redact: {exc}; nothing is written", file=sys.stderr)
        return 2
    except (extract.Unsupported, extract.NoText, review.StaleReview, KeyError, ValueError) as exc:
        print(f"redact: {exc}", file=sys.stderr)
        return 1
    if result.status == "review":
        print(f"redact: {result.open_items} span(s) need a decision: set each to \"redact\" or \"keep\" in "
              f"{target.name}.review.json and run again (or --no-review); nothing is written yet", file=sys.stderr)
        return 3
    found = ", ".join(f"{t} {n}" for t, n in sorted(result.counts.items())) or "nothing found"
    print(f"redact: {src.name} -> {target} ({found})", file=sys.stderr)
    return 0


def _run_dir(args, src: Path) -> int:
    from . import app
    out = Path(args.out) if args.out else src.with_name(src.name + ".redacted")
    regions = tuple(r.strip().lower() for r in args.regions.split(",") if r.strip()) if args.regions else None
    try:
        summary = app.run_dir(src, out, _model_detectors(args), regions, interactive=sys.stdin.isatty(),
                              recursive=args.recursive, ask=_ask, no_review=args.no_review,
                              drop_columns=frozenset(args.drop_column),
                              log=lambda line: print(f"redact: {line}", file=sys.stderr))
    except RuntimeError as exc:
        print(f"redact: {exc}; nothing is written", file=sys.stderr)
        return 2
    except (review.StaleReview, KeyError, ValueError) as exc:
        print(f"redact: {exc}", file=sys.stderr)
        return 1
    found = ", ".join(f"{t} {n}" for t, n in sorted(summary.counts.items())) or "nothing found"
    print(f"redact: {src} -> {out}: {summary.written} written, {summary.review} waiting on review, "
          f"{summary.skipped} skipped, {summary.exists} already there ({found})", file=sys.stderr)
    return 3 if summary.review else 0
