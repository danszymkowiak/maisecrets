"""Personal terms (docs/TERMS.md): the parser of ``terms.txt`` and its loader.

``parse`` is pure: text in, entities out. ``load`` reads the file and refuses one that the group
or others can read. Every error names the line number, never the text of a line: the file holds
the names the person keeps from the model.
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

WORD = "word"        # Jan: no letter or digit on either side
STARTS = "starts"    # Kowalsk*: word start, any ending
ENDS = "ends"        # *kowalski: any start, word end
INSIDE = "inside"    # *kowalski*: anywhere

MIN_INSIDE = 4       # *x* shorter than this would replace half of every text
LABEL_RE = re.compile(r"[A-Z][A-Z_]{0,31}")


class TermsError(ValueError):
    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.line = line


@dataclass(frozen=True)
class Variant:
    text: str
    mode: str


@dataclass(frozen=True)
class Entity:
    label: str
    variants: tuple[Variant, ...]
    line: int

    @property
    def canonical(self) -> str | None:
        """The form a placeholder resolves to: the first variant without a ``*``."""
        return next((v.text for v in self.variants if v.mode == WORD), None)


def _variant(raw: str, n: int) -> Variant:
    text = raw.strip()
    starts, ends = text.startswith("*"), text.endswith("*") and len(text) > 1
    text = text[1 if starts else 0:len(text) - 1 if ends else len(text)].strip()
    if not text:
        raise TermsError(f"line {n}: an empty variant", n)
    if "*" in text:
        raise TermsError(f"line {n}: a * may stand only at the start or the end of a variant", n)
    text = " ".join(text.split())
    if starts and ends:
        if len(text) < MIN_INSIDE:
            raise TermsError(f"line {n}: a *…* variant needs at least {MIN_INSIDE} characters", n)
        return Variant(text, INSIDE)
    return Variant(text, STARTS if ends else ENDS if starts else WORD)


def parse(text: str, reserved: frozenset[str] = frozenset()) -> list[Entity]:
    """Entities of a ``terms.txt``; ``reserved`` are the types the detector already uses."""
    entities: list[Entity] = []
    seen: set[str] = set()
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        label, rest = parts[0], parts[1] if len(parts) > 1 else ""
        if not LABEL_RE.fullmatch(label):
            raise TermsError(f"line {n}: the line must start with a label of capital letters and _ "
                             "(at most 32), then the variants", n)
        if label in reserved:
            raise TermsError(f"line {n}: the label is a type the detector already uses", n)
        if label in seen:
            raise TermsError(f"line {n}: the label appears on an earlier line", n)
        seen.add(label)
        entities.append(Entity(label, tuple(_variant(v, n) for v in rest.split("|")), n))
    return entities


def default_path() -> Path:
    from . import vault
    return vault.HOME / "terms.txt"


def load(path: Path | None = None, reserved: frozenset[str] = frozenset()) -> list[Entity]:
    """Entities of the term file; no file, no terms. Raises TermsError: the caller fails closed."""
    path = Path(path) if path is not None else default_path()
    try:
        st = path.stat()
    except FileNotFoundError:
        return []
    if os.name != "nt" and st.st_mode & 0o077:
        raise TermsError(f"{path}: mode {stat.S_IMODE(st.st_mode):04o} lets others read it; "
                         f"run chmod 600 {path}")
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        raise TermsError(f"{path}: not UTF-8 text") from None
    except OSError as exc:
        raise TermsError(f"{path}: cannot read it ({type(exc).__name__})") from None
    try:
        return parse(text, reserved)
    except TermsError as exc:
        raise TermsError(f"{path}: {exc}", exc.line) from None
