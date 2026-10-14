"""Local PII models behind one interface (TASK-34.4). A backend turns a chunk of text into (start, end, label, score)
tuples; detector_from() chunks long texts with overlap, maps the labels to the tool's types and returns a pipeline
detector. The libraries (gliner, transformers, torch) are an optional extra; nothing is sent to a remote API, and a
model is downloaded once into the Hugging Face cache outside the repository.

Licences (read from each model's Hugging Face record, 2026-10-12): only permissive ones are defaults; a model with
restrictive terms runs only when its id is passed to accept its terms (memory: public fork licensing).
"""
from __future__ import annotations

import bisect
import json
import os
import re
import warnings
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Callable, Iterator, Mapping, Protocol

from .pipeline import Detector, Document, Span


class Backend(Protocol):
    def spans(self, text: str) -> list[tuple[int, int, str, float]]: ...


# the labels asked of zero-shot models, and every label a model may answer with -> the tool's type
QUERY_LABELS = ("person", "street address", "email", "phone number", "date of birth", "bank account number",
                "national id number", "passport number", "tax id")
LABELS = {
    "person": "NAME", "name": "NAME", "per": "NAME", "private_person": "NAME", "first_name": "NAME",
    "last_name": "NAME", "street address": "ADDRESS", "address": "ADDRESS", "private_address": "ADDRESS",
    "email": "EMAIL", "email address": "EMAIL", "private_email": "EMAIL", "phone number": "PHONE", "phone": "PHONE",
    "private_phone": "PHONE", "date of birth": "DOB",
    # openai/privacy-filter's private_date: a date about a person, in documents mostly a birth date; unmapped until
    # 2026-10-12, so every date it found was dropped (TASK-34.8)
    "private_date": "DOB", "bank account number": "ACCOUNT", "account_number": "ACCOUNT",
    "national id number": "NATIONAL_ID", "passport number": "PASSPORT", "tax id": "TAX_ID",
    # gliner2's own label names (fastino/gliner2-privacy-filter-PII-multi lists 42)
    "full_name": "NAME", "street_address": "ADDRESS", "phone_number": "PHONE", "date_of_birth": "DOB",
    "iban": "ACCOUNT", "bank_account": "ACCOUNT", "national_id_number": "NATIONAL_ID",
    "passport_number": "PASSPORT", "tax_id": "TAX_ID", "tax_number": "TAX_ID",
}
# gliner2 is asked in its own label names: with "person" alone it found "Erika" and not "Erika Musterfrau" (2026-10-12)
GLINER2_QUERY_LABELS = ("person", "full_name", "street_address", "email", "phone_number", "date_of_birth", "iban",
                        "bank_account", "national_id_number", "passport_number", "tax_id")


# GLiNER's word splitter (gliner.data_processing.tokenizer.WhitespaceTokenSplitter): what its max_len counts
WORD_RE = re.compile(r"\w+(?:[-_]\w+)*|\S")


def windows(text: str, chunk: int, overlap: int, max_words: int | None = None) -> Iterator[tuple[int, int]]:
    """(start, end) of each chunk: `chunk` characters overlapping by `overlap`, and with `max_words` no more words
    than that, so a model that drops words past its limit sees every word in some chunk. A chunk cut by the word cap
    ends at a word start and the next one starts a sixth of the cap earlier."""
    starts = [m.start() for m in WORD_RE.finditer(text)] if max_words else []
    at = 0
    while True:
        end = min(len(text), at + chunk)
        k = bisect.bisect_left(starts, at)
        cut = bool(max_words) and len(starts) - k > max_words and starts[k + max_words] < end
        if cut:
            end = starts[k + max_words]
        yield at, end
        if end >= len(text):
            return
        if cut:
            nxt = starts[max(k + 1, k + max_words - max(1, max_words // 6))]
        else:
            nxt = at + max(1, chunk - overlap)
        at = max(at + 1, nxt)


def detector_from(backend: Backend, name: str, chunk: int = 2000, overlap: int = 200) -> Detector:
    """A detector over chunks of `chunk` characters that overlap by `overlap` (and of at most the backend's
    `max_words` words, see windows). A span touching the cut edge of a chunk is left to the neighbour that holds it
    whole; the same span from two chunks is kept once."""
    max_words = getattr(backend, "max_words", None)

    def find(doc: Document) -> list[Span]:
        text, seen, out = doc.text, set(), []
        for at, end in windows(text, chunk, overlap, max_words):
            part = text[at:end]
            last = end >= len(text)
            for a, b, label, score in backend.spans(part):
                if (b >= len(part) and not last) or (a == 0 and at > 0):
                    continue
                kind = LABELS.get(label.strip().lower())
                key = (at + a, at + b, kind)
                if kind and key not in seen:
                    seen.add(key)
                    out.append(Span(at + a, at + b, kind, name, float(score)))
        return sorted(out, key=lambda s: (s.start, -s.end))
    return find


class GlinerBackend:
    """The gliner library (Apache-2.0): zero-shot span labels. Its use against real models is measured in TASK-34.8."""
    max_words = 320     # GLiNER drops words past max_len (384); its label prompt takes room too

    def __init__(self, model_id: str, threshold: float = 0.5) -> None:
        from gliner import GLiNER
        self.model, self.threshold = GLiNER.from_pretrained(model_id), threshold

    def spans(self, text: str):
        return [(e["start"], e["end"], e["label"], e["score"])
                for e in self.model.predict_entities(text, list(QUERY_LABELS), threshold=self.threshold)]


def merge_pieces(text: str, pieces: list[tuple[int, int, str, float]]) -> list[tuple[int, int, str, float]]:
    """Trim whitespace off each piece, then join pieces of one label that touch or lie a space or tab apart on one
    line (score: the lowest). openai/privacy-filter answers ' Erika Muster' and 'frau' for one name (2026-10-12)."""
    out: list[tuple[int, int, str, float]] = []
    for a, b, label, score in sorted(pieces):
        while a < b and text[a].isspace():
            a += 1
        while b > a and text[b - 1].isspace():
            b -= 1
        if a == b:
            continue
        if out and out[-1][2] == label and out[-1][1] <= a and not text[out[-1][1]:a].strip(" \t"):
            pa, _, _, ps = out[-1]
            out[-1] = (pa, b, label, min(ps, score))
        else:
            out.append((a, b, label, score))
    return out


class TokenClassificationBackend:
    """A Hugging Face token-classification model (transformers, Apache-2.0), words merged into entities."""

    def __init__(self, model_id: str) -> None:
        from transformers import pipeline
        self.pipe = pipeline("token-classification", model=model_id, aggregation_strategy="simple")

    def spans(self, text: str):
        return merge_pieces(text, [(e["start"], e["end"], str(e["entity_group"]), float(e["score"]))
                                   for e in self.pipe(text)])


def gliner2_spans(result: dict) -> list[tuple[int, int, str, float]]:
    return [(int(e["start"]), int(e["end"]), label, float(e["confidence"]))
            for label, found in result.get("entities", {}).items() for e in found]


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


@dataclass(frozen=True)
class Model:
    backend: str
    licence: str
    source: str
    note: str = ""


def _hf(mid: str) -> str:
    return f"https://huggingface.co/{mid}"


MODELS: dict[str, Model] = {
    "urchade/gliner_multi_pii-v1": Model("gliner", "apache-2.0", _hf("urchade/gliner_multi_pii-v1"),
                                         "multilingual GLiNER fine-tuned for PII"),
    "knowledgator/gliner-pii-base-v1.0": Model("gliner", "apache-2.0", _hf("knowledgator/gliner-pii-base-v1.0")),
    "openai/privacy-filter": Model("token-classification", "apache-2.0", _hf("openai/privacy-filter"),
                                   "1.5B parameters, 50M active; a bidirectional token classifier"),
    "fastino/gliner2-privacy-filter-PII-multi": Model("gliner2", "apache-2.0",
                                                      _hf("fastino/gliner2-privacy-filter-PII-multi"),
                                                      "the spec's benchmark leader"),
    "gretelai/gretel-gliner-bi-large-v1.0": Model("gliner", "apache-2.0", _hf("gretelai/gretel-gliner-bi-large-v1.0")),
    "nvidia/gliner-PII": Model("gliner", "nvidia-open-model-license", _hf("nvidia/gliner-PII"),
                               "for clinical text; NVIDIA's own terms, not an OSI licence: opt-in"),
    "iiiorg/piiranha-v1-detect-personal-information": Model(
        "token-classification", "cc-by-nc-nd-4.0", _hf("iiiorg/piiranha-v1-detect-personal-information"),
        "non-commercial, no derivatives: opt-in; weak on financial text (spec)"),
}
PERMISSIVE = frozenset({"apache-2.0", "mit", "bsd-3-clause", "bsd-2-clause"})
# the default vote (user, 2026-10-12; TASK-34.8, docs/REDACT.md): all four permissive models, a span is redacted when
# two of them find it, and a span only privacy-filter finds is dropped rather than asked about. On the bench: names
# 88 %, addresses 90 %, birth dates 100 %, 7.2 false redactions and 9 review questions per 1,000 words
DEFAULTS = ("urchade/gliner_multi_pii-v1", "knowledgator/gliner-pii-base-v1.0",
            "fastino/gliner2-privacy-filter-PII-multi", "openai/privacy-filter")
VOTE_K = 2
NOT_REVIEWED = ("openai/privacy-filter",)


class TermsNotAccepted(ValueError):
    """A model with restrictive terms was asked for without accepting them."""


def check_terms(model_ids: list[str], accepted: tuple[str, ...]) -> None:
    for mid in model_ids:
        if mid not in MODELS:
            raise KeyError(f"{mid}: not a known model ({', '.join(sorted(MODELS))})")
        m = MODELS[mid]
        if m.licence not in PERMISSIVE and mid not in accepted:
            raise TermsNotAccepted(f"{mid} is under {m.licence} ({m.source}); read the terms and pass "
                                   f"--accept-model-terms {mid} to use it")


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
