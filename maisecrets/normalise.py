"""A cleaned copy of a text for the shape rules, with a map back to the original (TASK-11.25).

A value the model reads can be split or disguised by what a terminal or a renderer hides: an ANSI colour reset or a
zero-width space inside a token, a lone carriage return of a progress line, the gutter of `cat -n`, `grep -n` or a
diff, an HTML entity or a markdown escape, fullwidth forms. Each stage removes or decodes one of them; the result
keeps, per character, the range of the original it came from, so a span found in the copy redacts the true text
(with whatever was hidden inside it).

A lone carriage return is deleted, not rendered: rendering the overwrite would hide the first half of a value the
model still reads. Homoglyphs stay: folding them needs a confusables table and they are a different risk.

Pure functions, the standard library only. Text that no stage changes comes back as the same object."""
from __future__ import annotations

import html
import re

# decode after the stages that clean a run's characters (maisecrets/decode.py, TASK-11.26); unwrap last: it asks the
# shape rules whether a token runs across a line break, on text the other stages cleaned
STAGES = ("ansi", "cr", "invisible", "gutter", "entity", "escape", "fullwidth", "decode", "unwrap")

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
_CR_RE = re.compile(r"\r(?!\n)")
_INVISIBLE_RE = re.compile(r"[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")
_CAT_N_RE = re.compile(r"^ *\d+\t", re.M)
# grep -n: path:12: on a match, path-13- on a context line; the path names a file (a dot or a slash in it)
_GREP_RE = re.compile(r"^(?=[^\s:]*[./])[\w./-]+?(?::\d+:|-\d+-)", re.M)
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_ENTITY_RE = re.compile(r"&(?:#\d{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|])")
_FULLWIDTH_RE = re.compile(r"[\uff01-\uff5e]")


class Normalised:
    """The cleaned text; starts[i] and ends[i] are the original range of its character i (None: unchanged)."""
    __slots__ = ("text", "starts", "ends")

    def __init__(self, text: str, starts: list[int] | None = None, ends: list[int] | None = None):
        self.text, self.starts, self.ends = text, starts, ends

    def span(self, a: int, b: int) -> tuple[int, int]:
        """The original range under the cleaned span [a, b), b > a."""
        if self.starts is None:
            return a, b
        return self.starts[a], self.ends[b - 1]


def _sub(text: str, rx: re.Pattern, repl) -> tuple[str, list[int], list[int]] | None:
    """text with every match replaced by repl(match); per output character, its range in text. None: no match."""
    out: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    pos = 0
    for m in rx.finditer(text):
        a, b = m.span()
        new = repl(m)
        if new == m.group(0):
            continue
        out.append(text[pos:a])
        starts.extend(range(pos, a))
        ends.extend(range(pos + 1, a + 1))
        out.append(new)
        starts.extend([a] * len(new))
        ends.extend([b] * len(new))
        pos = b
    if not out:
        return None
    out.append(text[pos:])
    starts.extend(range(pos, len(text)))
    ends.extend(range(pos + 1, len(text) + 1))
    return "".join(out), starts, ends


def _diff_gutter(text: str) -> tuple[str, list[int], list[int]] | None:
    """The first column of every line inside a unified diff hunk, after its @@ header."""
    if "@@" not in text:
        return None
    out: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    in_hunk = changed = False
    pos = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        cut = 0
        if _HUNK_RE.match(body):
            in_hunk = True
        elif in_hunk and body[:1] in (" ", "+", "-") and not body.startswith(("+++ ", "--- ")):
            cut = 1
        elif in_hunk and not body.startswith("\\"):
            in_hunk = False
        out.append(line[cut:])
        starts.extend(range(pos + cut, pos + len(line)))
        ends.extend(range(pos + cut + 1, pos + len(line) + 1))
        changed = changed or cut > 0
        pos += len(line)
    return ("".join(out), starts, ends) if changed else None


def _gutter(text: str):
    steps = [s for s in (_sub(text, _CAT_N_RE, lambda m: ""),) if s]
    cur = steps[0][0] if steps else text
    grep = _sub(cur, _GREP_RE, lambda m: "")
    if grep:
        steps.append(grep)
        cur = grep[0]
    diff = _diff_gutter(cur)
    if diff:
        steps.append(diff)
    return steps


def _entity(m: re.Match) -> str:
    got = html.unescape(m.group(0))
    return got if len(got) == 1 else m.group(0)


def _stage(name: str, text: str) -> list:
    """The steps of one stage: each (text, starts, ends) relative to the previous step."""
    if name == "ansi":
        return [s for s in (_sub(text, _ANSI_RE, lambda m: ""),) if s] if "\x1b" in text else []
    if name == "cr":
        return [s for s in (_sub(text, _CR_RE, lambda m: ""),) if s] if "\r" in text else []
    if name == "invisible":
        return [] if text.isascii() else [s for s in (_sub(text, _INVISIBLE_RE, lambda m: ""),) if s]
    if name == "gutter":
        return _gutter(text)
    if name == "entity":
        return [s for s in (_sub(text, _ENTITY_RE, _entity),) if s] if "&" in text else []
    if name == "escape":
        return [s for s in (_sub(text, _ESCAPE_RE, lambda m: m.group(1)),) if s] if "\\" in text else []
    if name == "fullwidth":
        return [] if text.isascii() else [
            s for s in (_sub(text, _FULLWIDTH_RE, lambda m: chr(ord(m.group(0)) - 0xFEE0)),) if s]
    if name == "decode":
        from . import decode
        budget = decode.Budget()
        got = _sub(text, decode.RUN_RE, lambda m: decode.decode_run(m.group(0), decode.MAX_DEPTH, budget) or m.group(0))
        return [got] if got else []
    if name == "unwrap":
        if "\n" not in text:
            return []
        from .unwrap import unwrap
        n = unwrap(text)
        return [] if n.starts is None else [(n.text, n.starts, n.ends)]
    raise ValueError(f"unknown normaliser stage {name!r}")


def normalise(text: str, stages=STAGES) -> Normalised:
    """The text after the named stages, in the order of STAGES, with its map back to text."""
    cur = text
    starts: list[int] | None = None
    ends: list[int] | None = None
    for name in STAGES:
        if name not in stages:
            continue
        for new, s, e in _stage(name, cur):
            if starts is None:
                starts, ends = s, e
            else:
                starts, ends = [starts[i] for i in s], [ends[j - 1] for j in e]
            cur = new
    unknown = set(stages) - set(STAGES)
    if unknown:
        raise ValueError(f"unknown normaliser stage {sorted(unknown)[0]!r}")
    return Normalised(cur, starts, ends)
