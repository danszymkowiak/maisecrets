"""The redact command: the only place that reads and writes files (docs/REDACT.md)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, extract, pipeline


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="redact", description="Extract the text of a document (PDF, CSV, Excel, text) and redact personal data "
                                   "and secrets in it, before the text goes to a language model. See docs/REDACT.md.")
    ap.add_argument("path", metavar="PATH", help="a file, or a directory to redact every supported file in")
    ap.add_argument("--out", metavar="DIR", help="where the redacted text goes (default: next to the input)")
    ap.add_argument("--regions", metavar="LIST",
                    help="country rules, comma-separated (for example ch,de); default: your maisecrets config")
    ap.add_argument("--drop-column", metavar="HEADER", action="append", default=[],
                    help="leave a CSV or Excel column out by its header (repeatable)")
    ap.add_argument("--rules-only", action="store_true", help="the plugin's rules alone, no local models")
    ap.add_argument("--version", action="version", version=f"redact {__version__}")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    from . import rules  # noqa: F401  registers the deterministic pass
    if not pipeline.available_detectors():
        print("redact: no detector is available, so nothing is written", file=sys.stderr)
        return 2
    src = Path(args.path)
    if not src.is_file():
        print(f"redact: {src}: not a file (directories come with TASK-34.6)", file=sys.stderr)
        return 2
    target = Path(args.out) / (src.name + ".redacted.txt") if args.out else src.with_name(src.name + ".redacted.txt")
    if target.exists():
        print(f"redact: {target} exists; nothing is overwritten", file=sys.stderr)
        return 1
    regions = tuple(r.strip().lower() for r in args.regions.split(",") if r.strip()) if args.regions else None
    try:
        doc = extract.extract(src, drop_columns=set(args.drop_column))
    except (extract.Unsupported, extract.NoText) as exc:
        print(f"redact: {exc}", file=sys.stderr)
        return 1
    try:
        find = rules.detector(regions=regions)
    except RuntimeError as exc:      # no maisecrets checkout to take the rules from
        print(f"redact: {exc}; nothing is written", file=sys.stderr)
        return 2
    if not args.rules_only:
        from . import models
        reason = models.unavailable_reason()
        if reason:
            print(f"redact: {reason}", file=sys.stderr)
    names = rules.Placeholders()
    spans = pipeline.detect(doc, [find])
    text = pipeline.render(doc, spans, names.placeholder)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    found = ", ".join(f"{t} {n}" for t, n in sorted(names.counts().items())) or "nothing found"
    print(f"redact: {src.name} -> {target} ({found})", file=sys.stderr)
    return 0
