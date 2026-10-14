"""The model libraries (TASK-34.4, an optional extra): gliner, gliner2 and transformers behind the domain's Backend,
the Hugging Face cache, and the loading of the models."""
from __future__ import annotations

import json
import os
import warnings
from importlib.util import find_spec
from pathlib import Path
from typing import Callable, Mapping

from ..domain.document import Detector
from ..domain.models import (GLINER2_QUERY_LABELS, MODELS, QUERY_LABELS, Backend, check_terms, detector_from,
                             gliner2_spans, merge_pieces)


class GlinerBackend:
    """The gliner library (Apache-2.0): zero-shot span labels. Its use against real models is measured in TASK-34.8."""
    max_words = 320     # GLiNER drops words past max_len (384); its label prompt takes room too

    def __init__(self, model_id: str, threshold: float = 0.5) -> None:
        from gliner import GLiNER
        self.model, self.threshold = GLiNER.from_pretrained(model_id), threshold

    def spans(self, text: str):
        return [(e["start"], e["end"], e["label"], e["score"])
                for e in self.model.predict_entities(text, list(QUERY_LABELS), threshold=self.threshold)]


class TokenClassificationBackend:
    """A Hugging Face token-classification model (transformers, Apache-2.0), words merged into entities."""

    def __init__(self, model_id: str) -> None:
        from transformers import pipeline
        self.pipe = pipeline("token-classification", model=model_id, aggregation_strategy="simple")

    def spans(self, text: str):
        return merge_pieces(text, [(e["start"], e["end"], str(e["entity_group"]), float(e["score"]))
                                   for e in self.pipe(text)])


class Gliner2Backend:
    """The gliner2 library (Apache-2.0), its local model class only: the package also holds a client for Fastino's
    hosted API (GLiNER2API), which the tool never constructs, so no text leaves the machine."""
    max_words = 320     # its encoder has a length limit too; the same cap as GLiNER

    def __init__(self, model_id: str, threshold: float = 0.5) -> None:
        from gliner2 import GLiNER2
        self.model, self.threshold = GLiNER2.from_pretrained(model_id), threshold

    def spans(self, text: str):
        return gliner2_spans(self.model.extract_entities(text, list(GLINER2_QUERY_LABELS), threshold=self.threshold,
                                                         include_confidence=True, include_spans=True))


BACKENDS: dict[str, Callable[[str], Backend]] = {
    "gliner": GlinerBackend, "token-classification": TokenClassificationBackend, "gliner2": Gliner2Backend,
}


REQUIRED = ("torch", "transformers", "gliner", "gliner2")


def unavailable_reason(has_module: Callable[[str], bool] = lambda name: find_spec(name) is not None) -> str | None:
    """None when the model extra is installed, else one line saying how to install it."""
    missing = [m for m in REQUIRED if not has_module(m)]
    if not missing:
        return None
    return (f"the local models are not installed ({', '.join(missing)} missing), so only the rules run; "
            "install them with: uv sync --project redact --extra models")


# what the libraries read at import: no progress bars, no advisories (the "unauthenticated requests" note, the
# transformers config notice); a setting of the person's own environment wins
_QUIET = {"HF_HUB_DISABLE_PROGRESS_BARS": "1", "HF_HUB_VERBOSITY": "error", "TRANSFORMERS_VERBOSITY": "error",
          "TRANSFORMERS_NO_ADVISORY_WARNINGS": "1", "HF_HUB_DISABLE_TELEMETRY": "1"}


def _hub_cache(env: Mapping[str, str]) -> Path:
    if env.get("HF_HUB_CACHE"):
        return Path(env["HF_HUB_CACHE"]).expanduser()
    home = env.get("HF_HOME") or str(Path(env.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "huggingface")
    return Path(home).expanduser() / "hub"


_CONFIGS = ("config.json", "gliner_config.json")


_WEIGHTS = ("*.safetensors", "*.bin", "*.onnx")


_TOKENIZERS = ("tokenizer.json", "tokenizer_config.json", "spm.model", "vocab.txt")


def _snapshot(cache: Path, model_id: str) -> Path | None:
    """The snapshot the libraries load offline: the one refs/main names, or the only one."""
    repo = cache / ("models--" + model_id.replace("/", "--"))
    ref = repo / "refs" / "main"
    if ref.is_file():
        d = repo / "snapshots" / ref.read_text(encoding="utf-8").strip()
        return d if d.is_dir() else None
    snaps = list((repo / "snapshots").glob("*"))
    return snaps[0] if len(snaps) == 1 else None


def _has(d: Path, names) -> bool:
    return any(p.exists() for n in names for p in d.glob(n))     # exists(): a link into blobs/ that is there


def cached(model_id: str, cache: Path) -> bool:
    """Is the model complete in the cache (TASK-58): its snapshot holds a config and weights; a GLiNER model also
    needs its base encoder's config when it ships no tokenizer of its own, and a bi-encoder its labels encoder."""
    snap = _snapshot(cache, model_id)
    if snap is None or not _has(snap, _CONFIGS) or not _has(snap, _WEIGHTS):
        return False
    gliner = snap / "gliner_config.json"
    if not gliner.exists():
        return True
    try:
        cfg = json.loads(gliner.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    needs = [cfg.get("labels_encoder")] + ([] if _has(snap, _TOKENIZERS) else [cfg.get("model_name")])
    for dep in filter(None, needs):
        d = _snapshot(cache, dep)
        if d is None or not (d / "config.json").exists():
            return False
    return True


def library_env(model_ids: list[str], env: Mapping[str, str]) -> dict[str, str]:
    """The variables to set before the model libraries load. With every model complete in the local cache the Hub is
    not asked at all (HF_HUB_OFFLINE): text never leaves the machine anyway, and now no request does either."""
    out = {k: v for k, v in _QUIET.items() if k not in env}
    cache = _hub_cache(env)
    if "HF_HUB_OFFLINE" not in env and all(cached(mid, cache) for mid in model_ids):
        out["HF_HUB_OFFLINE"] = "1"
    return out


def load(model_ids: list[str], accepted: tuple[str, ...] = ()) -> list[Detector]:
    check_terms(model_ids, accepted)
    env = library_env(model_ids, os.environ)
    os.environ.update(env)
    with warnings.catch_warnings():
        # the libraries' own deprecations, nothing the person can act on (gliner passes resume_download)
        warnings.filterwarnings("ignore", message=".*resume_download.*")
        warnings.filterwarnings("ignore", message=".*torch.jit.script.*")
        out = []
        for mid in model_ids:
            try:
                out.append(detector_from(BACKENDS[MODELS[mid].backend](mid), mid))
            except Exception as exc:
                if "HF_HUB_OFFLINE" not in env:
                    raise
                raise RuntimeError(f"{mid} did not load with the Hugging Face Hub offline, which redact turned on "
                                   f"because the cache looked complete ({exc.__class__.__name__}); run once with "
                                   "HF_HUB_OFFLINE=0 to finish the download") from exc
        return out
