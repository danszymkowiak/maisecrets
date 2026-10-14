"""The ports of the bench's use cases (TASK-62): what a run, a mutation judgement, a round and a setup need from the
outside, as Protocols. The adapters implement them; adapters/compose.py puts one of each into a BenchPorts bundle."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from ..domain.floors import Floors
from ..domain.mutation import Mutation
from ..domain.samples import Sample


class Files(Protocol):
    def read_text(self, path: Path) -> str: ...

    def write_text(self, path: Path, text: str) -> None: ...     # makes the parent folder

    def exists(self, path: Path) -> bool: ...

    def glob(self, folder: Path, pattern: str) -> list[Path]: ...

    def replace(self, src: Path, dst: Path) -> None: ...


class SampleStore(Protocol):
    def read(self, path: Path) -> list[Sample]: ...

    def write(self, samples: list[Sample], path: Path) -> None: ...   # checks every sample first


class DetectionStore(Protocol):
    def save(self, det: dict, path: Path) -> None: ...

    def load(self, path: Path) -> dict: ...


class Detector(Protocol):
    """The plugin's detector, run in worker processes per language group."""

    def detect(self, samples: list[Sample], jobs: int, mutation: Mutation | None = None) -> tuple[dict, dict]: ...

    def rule_index(self) -> dict: ...

    def validate(self, mutation: Mutation) -> None: ...

    def gold_checks(self) -> dict: ...


@dataclass(frozen=True)
class BenchPorts:
    files: Files
    samples: SampleStore
    detections: DetectionStore
    detector: Detector
    floors: Callable[[], Floors]
    exceptions: Callable[[Path | None], list[dict]]     # the reviewed gold exceptions; None: the repository's file
