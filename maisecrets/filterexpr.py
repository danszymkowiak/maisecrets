"""The evaluator of Betterleaks rule filters (TASK-19.2).

scripts/sync_betterleaks.py turns each filter expression into a JSON tree of nested lists (its docstring lists the
node kinds); this module evaluates such a tree for one finding. A filter that evaluates to `true` discards the
finding, as in Betterleaks. Pure: no I/O, no state but a cache of compiled patterns.

Where it differs from Betterleaks:
- offsets are character offsets into the scanned text, not byte offsets; the filters only cut windows with them;
- `tokenRatio` needs a tokenizer the standard library lacks: it is UNKNOWN, and a comparison with UNKNOWN is false, so
  `entropy(s) < 3.0 || tokenRatio(s) >= 2.5` falls back to its entropy limit (TASK-19.3 decides);
  `failsTokenEfficiency` is false for the same reason;
- a filter that fails (a type error, a missing field) keeps the finding: a hit nobody could judge stays redacted.
"""
from __future__ import annotations

import re


class _Unknown:
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNKNOWN"


UNKNOWN = _Unknown()
_PATTERNS: dict[str, re.Pattern[str]] = {}


def _rx(pattern: str) -> re.Pattern[str]:
    rx = _PATTERNS.get(pattern)
    if rx is None:
        from .detect import _re2_to_python
        rx = _PATTERNS[pattern] = re.compile(_re2_to_python(pattern))
    return rx


def _entropy(s: str) -> float:
    from .detect import shannon_entropy
    return shannon_entropy(s)


def _str(v) -> str:
    if not isinstance(v, str):
        raise TypeError(f"not a string: {v!r}")
    return v


FUNCTIONS = {
    "entropy": lambda s: _entropy(_str(s)),
    "tokenRatio": lambda s: UNKNOWN,
    "failsTokenEfficiency": lambda s: False,
    "matchesAny": lambda s, pats: any(_rx(p).search(_str(s)) for p in pats),
    "containsAny": lambda s, terms: any(t in _str(s) for t in terms),
    "findMatch": lambda s, p: (lambda m: m.group(0) if m else "")(_rx(p).search(_str(s))),
    "len": len,
    "max": max,
    "min": min,
    "split": lambda s, sep: _str(s).split(sep),
    "join": lambda items, sep: sep.join(items),
    "lower": lambda s: _str(s).lower(),
    "setConfidence": lambda level: None,     # the detector has no confidence levels (yet)
}

_COMPARE = {
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
    "in": lambda a, b: a in b,
    "contains": lambda a, b: _str(b) in _str(a),
    "matches": lambda a, b: bool(_rx(_str(b)).search(_str(a))),
    "startsWith": lambda a, b: _str(a).startswith(_str(b)),
    "endsWith": lambda a, b: _str(a).endswith(_str(b)),
}
_ARITH = {
    "+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b,
    "/": lambda a, b: a / b, "%": lambda a, b: a % b,
}


def _int(v) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"not an index: {v!r}")
    return int(v)


def evaluate(node, env: dict):
    kind = node[0]
    if kind == "lit":
        return node[1]
    if kind == "var":
        if node[1] not in env:
            raise NameError(node[1])
        return env[node[1]]
    if kind == "list":
        return [evaluate(x, env) for x in node[1]]
    if kind == "index":
        obj, key = evaluate(node[1], env), evaluate(node[2], env)
        if isinstance(obj, dict):
            return obj.get(key)
        return obj[_int(key)]
    if kind == "slice":
        obj = evaluate(node[1], env)
        lo = None if node[2] is None else _int(evaluate(node[2], env))
        hi = None if node[3] is None else _int(evaluate(node[3], env))
        if not isinstance(obj, (str, list)):
            raise TypeError(f"cannot slice {obj!r}")
        return obj[lo:hi]
    if kind == "call":
        return FUNCTIONS[node[1]](*(evaluate(a, env) for a in node[2]))
    if kind == "un":
        x = evaluate(node[2], env)
        if x is UNKNOWN:
            return UNKNOWN
        if node[1] == "!":
            if not isinstance(x, bool):
                raise TypeError(f"! of {x!r}")
            return not x
        return -x
    if kind == "bin":
        op = node[1]
        if op in ("||", "&&"):
            a = evaluate(node[2], env)
            if a is True if op == "||" else a is False:
                return a
            return evaluate(node[3], env)
        if op == "??":
            a = evaluate(node[2], env)
            return evaluate(node[3], env) if a is None else a
        a, b = evaluate(node[2], env), evaluate(node[3], env)
        if op in _COMPARE:
            return False if a is UNKNOWN or b is UNKNOWN else _COMPARE[op](a, b)
        if a is UNKNOWN or b is UNKNOWN:
            return UNKNOWN
        if isinstance(a, str) != isinstance(b, str):
            raise TypeError(f"{a!r} {op} {b!r}")
        return _ARITH[op](a, b)
    if kind == "cond":
        test = evaluate(node[1], env)
        return evaluate(node[2] if test is True else node[3], env)
    if kind == "let":
        return evaluate(node[3], {**env, node[1]: evaluate(node[2], env)})
    raise ValueError(f"unknown node {kind!r}")


def finding(text: str, match_start: int, match_end: int, secret: str) -> dict:
    """The `finding` map a filter reads: the secret, the whole match, its line, the text and the offsets."""
    line_start = text.rfind("\n", 0, match_start) + 1
    line_end = text.find("\n", match_end)
    line_end = len(text) if line_end < 0 else line_end
    return {"secret": secret, "match": text[match_start:match_end], "line": text[line_start:line_end],
            "fragment_raw": text, "match_start_idx": match_start, "match_end_idx": match_end,
            "match_line_start_idx": line_start, "match_line_end_idx": line_end}


def discards(tree, found: dict, attributes: dict | None = None) -> bool:
    """Whether the filter drops this finding. A filter that fails keeps it."""
    try:
        return evaluate(tree, {"finding": found, "attributes": attributes or {"path": ""}}) is True
    except (TypeError, ValueError, NameError, KeyError, IndexError, AttributeError, re.error, ZeroDivisionError):
        return False
