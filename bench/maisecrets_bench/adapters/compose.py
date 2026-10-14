"""The composition root of the bench (TASK-62): the adapters put into the use cases' ports, behind the signatures the
scripts (bench/*.py) and the tests use. The plugin's detector is imported only when a call needs it, so importing
this module sets up no maisecrets home."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..application import mutate, round as rnd, run as run_case, setup
from ..application.ports import BenchPorts
from ..domain import validgold
from ..domain.floors import Floors
from ..domain.labels import LabelTable
from ..domain.mutation import RECALL_TOLERANCE, Mutation
from ..domain.samples import Sample, validate
from . import files, parquet_store


def _unknown_type(t: str) -> bool:
    from .plugin.pool import unknown_type
    return unknown_type(t)


def load_floors(path: Path | None = None) -> Floors:
    return files.load_floors(_unknown_type, path)


def load_labels(dataset: str, path: Path | None = None) -> LabelTable:
    return files.load_labels(dataset, _unknown_type, path)


def ports() -> BenchPorts:
    from .plugin.pool import PluginDetector
    return BenchPorts(files.LocalFiles(), parquet_store.ParquetStore(_unknown_type),
                      parquet_store.ParquetStore(_unknown_type), PluginDetector(), load_floors, files.load_exceptions)


def validate_sample(s: Sample) -> None:
    validate(s, _unknown_type)


def write_samples(samples: list[Sample], path: Path) -> None:
    parquet_store.write(samples, path, _unknown_type)


def mark_gold(samples: list[Sample]) -> tuple[list[Sample], dict]:
    from .plugin.gold import checks
    return validgold.mark(samples, checks())


def run(parquet: Path, datasets: list[str], out: Path, jobs: int, limit: int | None = None) -> dict:
    return run_case.run(ports(), parquet, datasets, out, jobs, limit)


def newest_full_run(runs_dir: Path, manifest: dict) -> Path:
    return run_case.newest_full_run(ports(), runs_dir, manifest)


def setup_run(sources: list[setup.Source], out: Path, log: Callable[[str], None] = lambda s: None,
              exceptions_file: Path | None = None) -> dict:
    return setup.run(ports(), sources, out, log, exceptions_file)


def baseline(run_dir: Path, parquet: Path) -> tuple[list, dict, list[str]]:
    return mutate.baseline(ports(), run_dir, parquet)


def mutated_detections(m: Mutation, samples: list, base_det: dict, jobs: int) -> tuple[dict, int]:
    return mutate.mutated_detections(ports(), m, samples, base_det, jobs)


def floor_summary(samples: list, det: dict, roles: dict, fl: Floors | None = None) -> dict:
    return mutate.floor_summary(samples, det, roles, fl or load_floors())


def evaluate(mutations: list[Mutation], samples: list, base_det: dict, roles: dict, jobs: int,
             recall_tolerance: float = RECALL_TOLERANCE) -> list[dict]:
    return mutate.evaluate(ports(), mutations, samples, base_det, roles, jobs, recall_tolerance)


def round_brief(run_dir: Path, parquet: Path, top: int = 15) -> str:
    return rnd.brief(ports(), run_dir, parquet, top)


def round_judge(mutations: list[Mutation], run_dir: Path, parquet: Path, roles: dict, jobs: int,
                recall_tolerance: float = RECALL_TOLERANCE) -> list[dict]:
    return rnd.judge(ports(), mutations, run_dir, parquet, roles, jobs, recall_tolerance)
