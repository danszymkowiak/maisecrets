"""The local PII models as data (TASK-34.4, TASK-34.8): their registry and licences, how their labels map to the
tool's types, the vote's defaults, and how a long text is cut into windows a model can read. The libraries themselves
are in adapters/model_backends.py."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Protocol

from .document import Detector, Document, Span


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
    than that as GLiNER counts them in the chunk itself (a word the chunk starts or ends inside may count as two), so
    a model that drops words past its limit sees every word in some chunk. A chunk cut by the word cap ends where its
    last word ends, and the next one starts a sixth of the cap earlier, in words: a span of up to max_words // 6
    words lies whole in one of the two (TASK-60)."""
    at = 0
    while True:
        end = min(len(text), at + chunk)
        tokens = list(WORD_RE.finditer(text, at, end)) if max_words else []
        cut = len(tokens) > (max_words or 0)
        if cut:
            end = tokens[max_words - 1].end()
        yield at, end
        if end >= len(text):
            return
        if cut:
            nxt = tokens[max(1, max_words - max(1, max_words // 6))].start()
        else:
            nxt = at + max(1, chunk - overlap)
        at = max(at + 1, nxt)


def detector_from(backend: Backend, name: str, chunk: int = 2000, overlap: int = 200) -> Detector:
    """A detector over chunks of `chunk` characters that overlap by `overlap` (and of at most the backend's
    `max_words` words, see windows). A span touching a chunk's cut end is left to the next chunk; a span at a later
    chunk's start is kept only when the earlier chunk could not hold it inside (it reaches the earlier chunk's end or
    past it): otherwise it is the earlier chunk's to find, and here may be the tail of a longer one (TASK-60). The
    same span from two chunks is kept once."""
    max_words = getattr(backend, "max_words", None)

    def find(doc: Document) -> list[Span]:
        text, seen, out, prev_end = doc.text, set(), [], 0
        for at, end in windows(text, chunk, overlap, max_words):
            part = text[at:end]
            last = end >= len(text)
            for a, b, label, score in backend.spans(part):
                if (b >= len(part) and not last) or (a == 0 and at > 0 and at + b < prev_end):
                    continue
                kind = LABELS.get(label.strip().lower())
                key = (at + a, at + b, kind)
                if kind and key not in seen:
                    seen.add(key)
                    out.append(Span(at + a, at + b, kind, name, float(score)))
            prev_end = end
        return sorted(out, key=lambda s: (s.start, -s.end))
    return find


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


def gliner2_spans(result: dict) -> list[tuple[int, int, str, float]]:
    return [(int(e["start"]), int(e["end"]), label, float(e["confidence"]))
            for label, found in result.get("entities", {}).items() for e in found]


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
