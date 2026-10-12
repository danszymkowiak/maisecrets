"""The redact command: the only place that reads and writes files (docs/REDACT.md)."""
from __future__ import annotations

import argparse
import sys

from . import __version__, pipeline


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="redact", description="Extract the text of a document (PDF, CSV, Excel, text) and redact personal data "
                                   "and secrets in it, before the text goes to a language model. See docs/REDACT.md.")
    ap.add_argument("path", metavar="PATH", help="a file, or a directory to redact every supported file in")
    ap.add_argument("--out", metavar="DIR", help="where the redacted text goes (default: next to the input)")
    ap.add_argument("--version", action="version", version=f"redact {__version__}")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not pipeline.available_detectors():
        print("redact: no detector is available yet, so nothing is written (the rules come with TASK-34.3)",
              file=sys.stderr)
        return 2
    print(f"redact: {args.path}: not implemented yet", file=sys.stderr)
    return 2
