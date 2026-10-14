"""The composition root of a run (TASK-62): the adapters put into the application's ports, behind the signatures the
command and the tests use (run_file, run_dir). The rules detector is built here, once per call."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..application import redact_file
from ..application.ports import Ports
from ..application.redact_file import DirSummary, Result
from ..domain.document import Detector
from ..domain.placeholders import Placeholders
from ..domain.review_items import Item
from . import extract, files, plugin_rules, review_file

from ..domain.outputs import output_name

__all__ = ["DirSummary", "Result", "output_name", "ports", "run_dir", "run_file"]


def ports(regions: tuple[str, ...] | None) -> Ports:
    return Ports(extract.FileExtractor(), plugin_rules.detector(regions=regions), review_file.ReviewFile(),
                 files.LocalSink(), files.LocalTree())


def run_file(src: Path, target: Path, model_detectors: dict[str, Detector], regions: tuple[str, ...] | None,
             interactive: bool, ask: Callable[[Item], str] | None = None, no_review: bool = False,
             drop_columns: frozenset[str] = frozenset(), names: Placeholders | None = None,
             vote_k: int | None = None, not_reviewed: tuple[str, ...] = ()) -> Result:
    return redact_file.run_file(ports(regions), src, target, model_detectors, interactive, ask, no_review,
                                drop_columns, names, vote_k, not_reviewed)


def run_dir(src: Path, out: Path, model_detectors: dict[str, Detector], regions: tuple[str, ...] | None,
            interactive: bool, recursive: bool = False, ask: Callable[[Item], str] | None = None,
            no_review: bool = False, drop_columns: frozenset[str] = frozenset(),
            log: Callable[[str], None] = lambda line: None, vote_k: int | None = None,
            not_reviewed: tuple[str, ...] = ()) -> DirSummary:
    return redact_file.run_dir(ports(regions), src, out, model_detectors, interactive, recursive, ask, no_review,
                               drop_columns, log, vote_k, not_reviewed)
