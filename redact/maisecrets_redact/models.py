"""Local PII models behind one interface (TASK-34.4). A backend turns a chunk of text into (start, end, label, score)
tuples; detector_from() chunks long texts with overlap, maps the labels to the tool's types and returns a pipeline
detector. The libraries (gliner, transformers, torch) are an optional extra; nothing is sent to a remote API, and a
model is downloaded once into the Hugging Face cache outside the repository.

Licences (read from each model's Hugging Face record, 2026-10-12): only permissive ones are defaults; a model with
restrictive terms runs only when its id is passed to accept its terms (memory: public fork licensing).
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Callable, Protocol

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
    "private_phone": "PHONE", "date of birth": "DOB", "bank account number": "ACCOUNT", "account_number": "ACCOUNT",
    "national id number": "NATIONAL_ID", "passport number": "PASSPORT", "tax id": "TAX_ID",
    # gliner2's own label names (fastino/gliner2-privacy-filter-PII-multi lists 42)
    "full_name": "NAME", "street_address": "ADDRESS", "phone_number": "PHONE", "date_of_birth": "DOB",
    "iban": "ACCOUNT", "bank_account": "ACCOUNT", "national_id_number": "NATIONAL_ID",
    "passport_number": "PASSPORT", "tax_id": "TAX_ID", "tax_number": "TAX_ID",
}
# gliner2 is asked in its own label names: with "person" alone it found "Erika" and not "Erika Musterfrau" (2026-10-12)
GLINER2_QUERY_LABELS = ("person", "full_name", "street_address", "email", "phone_number", "date_of_birth", "iban",
                        "bank_account", "national_id_number", "passport_number", "tax_id")


def detector_from(backend: Backend, name: str, chunk: int = 2000, overlap: int = 200) -> Detector:
    """A detector over chunks of `chunk` characters that overlap by `overlap`. A span touching the cut edge of a chunk
    is left to the neighbour that holds it whole; the same span from two chunks is kept once."""
    step = max(1, chunk - overlap)

    def find(doc: Document) -> list[Span]:
        text, seen, out = doc.text, set(), []
        at = 0
        while True:
            part = text[at:at + chunk]
            last = at + chunk >= len(text)
            for a, b, label, score in backend.spans(part):
                if (b >= len(part) and not last) or (a == 0 and at > 0):
                    continue
                kind = LABELS.get(label.strip().lower())
                key = (at + a, at + b, kind)
                if kind and key not in seen:
                    seen.add(key)
                    out.append(Span(at + a, at + b, kind, name, float(score)))
            if last:
                return sorted(out, key=lambda s: (s.start, -s.end))
            at += step
    return find


class GlinerBackend:
    """The gliner library (Apache-2.0): zero-shot span labels. Its use against real models is measured in TASK-34.8."""

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
# three permissive models of two families; TASK-34.8 chooses the final set from bench numbers
DEFAULTS = ("urchade/gliner_multi_pii-v1", "knowledgator/gliner-pii-base-v1.0", "openai/privacy-filter")


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


def load(model_ids: list[str], accepted: tuple[str, ...] = ()) -> list[Detector]:
    check_terms(model_ids, accepted)
    return [detector_from(BACKENDS[MODELS[mid].backend](mid), mid) for mid in model_ids]
