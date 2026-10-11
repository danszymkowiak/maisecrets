"""Recall under perturbation (docs/BENCHMARK.md, Perturbation): each transform rewrites every in-scope positive of a
fixed pick of samples per dataset, the detector runs on the rewritten text, and the report gives recall per
transform. It shows what a normaliser or a decode-and-rescan step would win; the scored runs never see it."""
from __future__ import annotations

import base64
import dataclasses
import hashlib
from typing import Callable

from . import score
from .schema import OUT_OF_SCOPE, Sample

_HOMOGLYPH = str.maketrans("aceopxyACEHKMOPTXB", "асеорхуАСЕНКМОРТХВ")   # Latin to Cyrillic look-alikes
_MD_SPECIAL = set("\\`*_{}[]()#+-.!|")


def _mid(v: str, insert: str) -> str:
    i = len(v) // 2
    return v[:i] + insert + v[i:]


TRANSFORMS: dict[str, Callable[[str], str]] = {
    "none": lambda v: v,
    "zero_width": lambda v: _mid(v, "​"),
    "soft_hyphen": lambda v: _mid(v, "­"),
    "fullwidth": lambda v: "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in v),   # NFKC folds it
    "homoglyph": lambda v: v.translate(_HOMOGLYPH),
    "ansi_reset": lambda v: _mid(v, "\x1b[0m"),          # grep --color and prompts split a value with a reset
    "cr": lambda v: _mid(v, "\r"),                       # a progress line overwritten in place
    "wrap": lambda v: _mid(v, "\n"),                     # a terminal or a tool wraps a long line
    "base64": lambda v: base64.b64encode(v.encode()).decode(),
    "hex": lambda v: v.encode().hex(),
    "entity": lambda v: "".join(f"&#{ord(c)};" for c in v),
    "escape": lambda v: "".join("\\" + c if c in _MD_SPECIAL else c for c in v),
    "truncation": lambda v: v[:max(1, (len(v) * 3) // 5)] + "…",     # a tool cuts the output short
}


def _in_scope(sp) -> bool:
    return sp.gold == "pos" and sp.maisecrets_type != OUT_OF_SCOPE


def rewrite(s: Sample, transform: Callable[[str], str]) -> Sample | None:
    """The sample with every in-scope positive transformed and every span moved with it; None when two in-scope
    positives overlap (one rewrite would cut the other)."""
    targets = sorted((sp for sp in s.spans if _in_scope(sp)), key=lambda sp: sp.start)
    if any(a.end > b.start for a, b in zip(targets, targets[1:])):
        return None
    edits = []     # (old start, old end, new value)
    for sp in targets:
        edits.append((sp.start, sp.end, transform(s.text[sp.start:sp.end])))
    parts, pos = [], 0
    shift_at = []  # (old start, old end, cumulative length change after that edit)
    shift = 0
    for a, b, new in edits:
        parts += [s.text[pos:a], new]
        pos = b
        shift += len(new) - (b - a)
        shift_at.append((a, b, shift))
    parts.append(s.text[pos:])

    def moved(i: int) -> int:
        d = 0
        for a, b, cum in shift_at:
            if i >= b:
                d = cum
        return i + d

    spans = []
    for sp in s.spans:
        edit = next(((a, b, new) for a, b, new in edits if (a, b) == (sp.start, sp.end)), None)
        if edit:
            start = moved(sp.start)
            spans.append(dataclasses.replace(sp, start=start, end=start + len(edit[2])))
        elif any(a < sp.end and sp.start < b for a, b, _ in edits):
            continue    # a span partly inside a rewritten value has no place in the new text
        else:
            spans.append(dataclasses.replace(sp, start=moved(sp.start), end=moved(sp.end)))
    return dataclasses.replace(s, text="".join(parts), spans=spans)


def pick(samples: list[Sample], n: int) -> list[Sample]:
    """Up to n samples with an in-scope positive, the same on every machine (by a hash of the sample id)."""
    have = [s for s in samples if any(_in_scope(sp) for sp in s.spans)]
    have.sort(key=lambda s: hashlib.sha256(f"perturb:{s.dataset}:{s.sample_id}".encode()).hexdigest())
    return have[:n]


def recall(samples: list[Sample], det: dict, unlabelled_negative: dict, judged: dict) -> dict:
    """{dataset: (found, positives)} over in-scope positives."""
    out: dict[str, list[int]] = {}
    for s in samples:
        c = score.score_sample(s, det.get((s.dataset, s.sample_id), []), unlabelled_negative.get(s.dataset, True),
                               judged.get(s.dataset))
        acc = out.setdefault(s.dataset, [0, 0])
        acc[0] += c.found
        acc[1] += c.found + c.fn
    return {k: (v[0], v[1]) for k, v in out.items()}


def report(table: dict, picked: dict) -> str:
    """table: {transform: {dataset: (found, positives)}}."""
    names = sorted({n for row in table.values() for n in row})
    out = ["# Recall under perturbation", "",
           "Each transform rewrites every in-scope positive of the picked samples; recall is over those positives. "
           "The change against `none` is in points.", "",
           "| transform | " + " | ".join(f"{n} ({picked.get(n, 0)} samples)" for n in names) + " |",
           "|---|" + "---|" * len(names)]
    base = table.get("none", {})
    for t, row in table.items():
        cells = []
        for n in names:
            found, total = row.get(n, (0, 0))
            r = found / total if total else None
            b = base.get(n, (0, 0))
            rb = b[0] / b[1] if b[1] else None
            if r is None:
                cells.append("n/a")
            elif t == "none" or rb is None:
                cells.append(f"{100 * r:.1f}%")
            else:
                cells.append(f"{100 * r:.1f}% ({100 * (r - rb):+.1f})")
        out.append(f"| {t} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"
