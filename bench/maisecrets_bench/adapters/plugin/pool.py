"""The plugin's detector over the samples, in worker processes per language group (docs/BENCHMARK.md, Regions): each
worker gets a fresh maisecrets home with the group's regions and locale before maisecrets loads, so a run is the
same on every machine. This module imports the detector only inside a worker or a call: a spawned worker imports it
first, before its home is set. Implements the Detector port (PluginDetector)."""
from __future__ import annotations

import json
import multiprocessing
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ...domain import score
from ...domain.bench_error import BenchError
from ...domain.mutation import Mutation
from ...domain.run_report import SKIP_TYPES, _group_config, group_of
from ...domain.samples import Sample


# workers start over pipes: forkserver, Python 3.14's default on Linux, needs a Unix socket that the Claude Code sandbox
# denies; spawn is the default on macOS and Windows, and each worker sets itself up in _init_worker anyway
POOL_CONTEXT = multiprocessing.get_context("spawn")


_detect = None


_RULESET = None     # this worker's rule set when a mutation is applied (bench only); None: the config's


def _init_worker(regions: list[str], locale: str, mutation=None) -> None:
    """A fresh home with the test store and the group's regions; the locale fixed; the rules mutated when a mutation
    is given (bench only, the plugin is not edited). Runs before maisecrets loads."""
    global _detect, _RULESET
    home = Path(tempfile.mkdtemp(prefix="maisecrets-bench-run-"))
    (home / "config.json").write_text(json.dumps({"backend": "jsonfile", "allow_plaintext_store": True,
                                                  "regions": regions}))
    os.environ["MAISECRETS_HOME"] = str(home)
    os.environ["MAISECRETS_LOCALE"] = locale
    from . import detector
    _detect = detector.detect
    if mutation is not None:
        from .mutations import ruleset
        _RULESET = ruleset(mutation, _detect.default_ruleset(), strict=False)   # validated over all regions before


def _detections(text: str) -> list[score.Detection]:
    # without a mutation scan(text) alone: an older maisecrets (MAISECRETS_BENCH_DETECTOR) has no ruleset keyword
    found = _detect.scan(text) if _RULESET is None else _detect.scan(text, ruleset=_RULESET)
    return [score.Detection(m.start, m.end, m.type, m.kind) for m in found if m.type not in SKIP_TYPES]


def _detect_chunk(chunk: list[Sample]) -> list[tuple[str, str, list[score.Detection]]]:
    return [(s.dataset, s.sample_id, _detections(s.text)) for s in chunk]


def _active(regions: list[str], locale: str, mutation=None) -> dict:
    """The rules, regions and label languages a group runs with, from a worker of its own."""
    with ProcessPoolExecutor(1, mp_context=POOL_CONTEXT, initializer=_init_worker,
                             initargs=(regions, locale, mutation)) as ex:
        return ex.submit(_describe).result()


def _describe() -> dict:
    a = _detect.active_regions()
    return {"regions": list(a.regions), "languages": list(a.languages),
            "rules": sorted({r.id for r in (_RULESET.rules if _RULESET is not None else _detect.rules())})}


def _require_rule_sets() -> None:
    """A mutation needs a maisecrets with rule sets (default_ruleset, scan(ruleset=)); an older one in
    MAISECRETS_BENCH_DETECTOR has none, and failed inside the process pool (TASK-61)."""
    from . import detector
    if not hasattr(detector.detect, "default_ruleset"):
        raise BenchError(f"a mutation needs a maisecrets with rule sets, and {detector.DETECTOR_REPO} "
                         "(MAISECRETS_BENCH_DETECTOR) has none; run mutations against this checkout")


def detect_samples(samples: list[Sample], jobs: int, chunk: int = 50, mutation=None) -> tuple[dict, dict]:
    """((dataset, sample_id) -> detections, group -> what it ran with)."""
    if mutation is not None:
        _require_rule_sets()
    by_lang: dict[str, list[Sample]] = {}
    for s in samples:
        by_lang.setdefault(group_of(s), []).append(s)
    det: dict[tuple[str, str], list[score.Detection]] = {}
    groups = {}
    for lang, group in sorted(by_lang.items()):
        regions, locale = _group_config(lang)
        groups[lang] = {**_active(regions, locale, mutation), "samples": len(group)}
        group.sort(key=lambda s: -len(s.text))      # the long files first: no straggler at the end
        chunks = [group[i:i + chunk] for i in range(0, len(group), chunk)]
        with ProcessPoolExecutor(jobs, mp_context=POOL_CONTEXT, initializer=_init_worker,
                                 initargs=(regions, locale, mutation)) as ex:
            for part in ex.map(_detect_chunk, chunks):
                for dataset, sample_id, ds in part:
                    det[(dataset, sample_id)] = ds
    return det, groups


class PluginDetector:
    """The Detector port: the groups in worker processes, and the rule index, the mutation check and the gold checks
    from the detector of this process."""

    def detect(self, samples: list[Sample], jobs: int, mutation: Mutation | None = None) -> tuple[dict, dict]:
        return detect_samples(samples, jobs, mutation=mutation)

    def rule_index(self) -> dict:
        from .detector import rule_index
        return rule_index()

    def validate(self, mutation: Mutation) -> None:
        from .mutations import validate
        validate(mutation)

    def gold_checks(self) -> dict:
        from .gold import checks
        return checks()


def unknown_type(t: str) -> bool:
    """The detector's check of a type name, imported on the first call."""
    from .detector import unknown_type as check
    return check(t)
