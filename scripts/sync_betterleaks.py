#!/usr/bin/env python3
"""Refresh the vendored Betterleaks ruleset to a pinned tag (TASK-19.1).

Usage: scripts/sync_betterleaks.py v1.9.0
Writes maisecrets/rules/betterleaks.toml (as upstream has it), betterleaks.json (what the detector reads),
LICENSE-betterleaks and BETTERLEAKS_VERSION. Nothing upstream runs: the TOML is read as data.

A rule's filter is an expression (CEL-style names such as filter.entropy in v1.9, Expr names such as entropy in
v2.0). parse() turns it into a JSON tree of nested lists, which the detector evaluates:

    ["lit", value]            ["var", name]               ["list", [items]]
    ["index", obj, key]       ["slice", obj, lo, hi]      ["call", function, [args]]
    ["un", op, x]             ["bin", op, a, b]           ["cond", test, then, else]
    ["let", name, value, body]

A function outside FUNCTIONS, an operator or a token it does not know, or a rule field outside RULE_FIELDS stops
the sync and names the rule: no rule is vendored without its filter. The live checks (validate, analyze, revoke)
are dropped: the threat model sends no secret anywhere to test it.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

FUNCTIONS = {"entropy", "tokenRatio", "failsTokenEfficiency", "matchesAny", "containsAny", "findMatch", "len",
             "max", "min", "split", "join", "lower", "setConfidence"}
ALIASES = {f"filter.{f}": f for f in FUNCTIONS}           # the v1.9 names
RULE_FIELDS = {"id", "description", "regex", "keywords", "confidence", "filter", "skipReport", "components",
               "secretGroup", "valueGroup", "path", "specificity", "entropy", "allowlists", "tags"}
DROPPED = {"validate", "analyze", "revoke"}
TOP_FIELDS = {"title", "minVersion", "betterleaksMinVersion", "prefilter", "filter", "rules", "extend"}


class SyncError(Exception):
    pass


_TOKEN_RE = re.compile(r"""
    (?P<ws>\s+|//[^\n]*)
  | (?P<num>\d+\.\d+|\d+)
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<raw>`[^`]*`)
  | (?P<name>[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)
  | (?P<op>\|\||&&|==|!=|<=|>=|\?\?|[<>!+\-*/%?:;,=()\[\]])
""", re.X)
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "0": "\0"}
_WORD_OPS = {"and": "&&", "or": "||", "not": "!", "in": "in", "contains": "contains", "matches": "matches",
             "startsWith": "startsWith", "endsWith": "endsWith"}
# binary operators, lowest precedence first
_LEVELS = [("??",), ("||",), ("&&",), ("==", "!="), ("<", "<=", ">", ">=", "in", "contains", "matches", "startsWith",
                                                   "endsWith"), ("+", "-"), ("*", "/", "%")]
_CONSTS = {"true": True, "false": False, "nil": None}


def _string(body: str) -> str:
    out, i = [], 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            if nxt == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", body[i + 2:i + 6]):
                out.append(chr(int(body[i + 2:i + 6], 16)))
                i += 6
                continue
            out.append(_ESCAPES.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(body[i])
            i += 1
    return "".join(out)


def _tokens(text: str, rule: str) -> list[tuple[str, object]]:
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise SyncError(f"{rule}: filter has an unknown token at {text[pos:pos + 20]!r}")
        pos = m.end()
        kind = m.lastgroup
        v = m.group(kind)
        if kind == "ws":
            continue
        if kind == "num":
            out.append(("lit", float(v) if "." in v else int(v)))
        elif kind == "str":
            out.append(("lit", _string(v[1:-1])))
        elif kind == "raw":
            out.append(("lit", v[1:-1]))
        elif kind == "name" and v in _WORD_OPS:
            out.append(("op", _WORD_OPS[v]))
        elif kind == "name" and v in _CONSTS:
            out.append(("lit", _CONSTS[v]))
        elif kind == "name" and v == "let":
            out.append(("let", v))
        else:
            out.append((kind, v))
    return out


class _Parser:
    def __init__(self, text: str, rule: str):
        self.rule = rule
        self.toks = _tokens(text, rule)
        self.i = 0

    def fail(self, why: str):
        near = " ".join(str(v) for _, v in self.toks[self.i:self.i + 4])
        raise SyncError(f"{self.rule}: filter {why} near {near!r}")

    def peek(self, kind=None, value=None) -> bool:
        if self.i >= len(self.toks):
            return False
        k, v = self.toks[self.i]
        return (kind is None or k == kind) and (value is None or v == value)

    def take(self, kind=None, value=None):
        if not self.peek(kind, value):
            self.fail(f"expects {value or kind}")
        self.i += 1
        return self.toks[self.i - 1][1]

    def program(self):
        tree = self.expr()
        if self.i != len(self.toks):
            self.fail("has text after the expression")
        return tree

    def expr(self):
        if self.peek("let"):
            self.take("let")
            name = self.take("name")
            self.take("op", "=")
            value = self.expr_no_let()
            self.take("op", ";")
            return ["let", name, value, self.expr()]
        return self.expr_no_let()

    def expr_no_let(self):
        test = self.binary(0)
        if self.peek("op", "?"):
            self.take("op", "?")
            then = self.expr_no_let()
            self.take("op", ":")
            return ["cond", test, then, self.expr_no_let()]
        return test

    def binary(self, level: int):
        if level == len(_LEVELS):
            return self.unary()
        left = self.binary(level + 1)
        while self.i < len(self.toks) and self.toks[self.i][0] == "op" and self.toks[self.i][1] in _LEVELS[level]:
            op = self.take()
            left = ["bin", op, left, self.binary(level + 1)]
        return left

    def unary(self):
        if self.peek("op", "!") or self.peek("op", "-"):
            op = self.take()
            return ["un", op, self.unary()]
        return self.postfix(self.primary())

    def args(self, close: str) -> list:
        items = []
        while not self.peek("op", close):
            items.append(self.expr())
            if not self.peek("op", close):
                self.take("op", ",")
        self.take("op", close)
        return items

    def postfix(self, node):
        while True:
            if self.peek("op", "["):
                self.take("op", "[")
                lo = None if self.peek("op", ":") else self.expr()
                if self.peek("op", ":"):
                    self.take("op", ":")
                    hi = None if self.peek("op", "]") else self.expr()
                    self.take("op", "]")
                    node = ["slice", node, lo, hi]
                else:
                    self.take("op", "]")
                    node = ["index", node, lo]
            elif self.peek("op", "(") and node[0] == "var":
                name = ALIASES.get(node[1], node[1])
                if name not in FUNCTIONS:
                    raise SyncError(f"{self.rule}: filter calls {node[1]!r}, which the detector does not know")
                self.take("op", "(")
                node = ["call", name, self.args(")")]
            else:
                return node

    def primary(self):
        if self.peek("lit"):
            return ["lit", self.take("lit")]
        if self.peek("name"):
            return ["var", self.take("name")]
        if self.peek("op", "("):
            self.take("op", "(")
            inner = self.expr()
            self.take("op", ")")
            return inner
        if self.peek("op", "["):
            self.take("op", "[")
            return ["list", self.args("]")]
        self.fail("expects a value")


def parse(text: str, rule: str):
    """The expression as a JSON tree; SyncError naming the rule on anything unknown."""
    return _Parser(text, rule).program()


def convert(toml_text: str) -> dict:
    cfg = tomllib.loads(toml_text)
    unknown = set(cfg) - TOP_FIELDS
    if unknown:
        raise SyncError(f"config: top-level field(s) {sorted(unknown)} unknown")
    out: dict = {"title": cfg.get("title", "")}
    for key in ("filter", "prefilter"):
        if cfg.get(key):
            out[key] = parse(cfg[key], f"config {key}")
    rules = []
    for r in cfg.get("rules", []):
        rid = r.get("id", "?")
        extra = set(r) - RULE_FIELDS - DROPPED
        if extra:
            raise SyncError(f"{rid}: rule field(s) {', '.join(repr(x) for x in sorted(extra))} unknown")
        rule = {k: v for k, v in r.items() if k in RULE_FIELDS and k not in ("filter", "valueGroup")}
        if "valueGroup" in r:
            rule["secretGroup"] = r["valueGroup"]
        if r.get("filter"):
            rule["filter"] = parse(r["filter"], rid)
        rules.append(rule)
    out["rules"] = rules
    return out


def main(argv: list[str]) -> int:
    import urllib.request
    tag = argv[0] if argv else None
    if not tag or not re.fullmatch(r"v\d+\.\d+\.\d+(?:-rc\.\d+)?", tag):   # it becomes part of a URL
        print("usage: sync_betterleaks.py vX.Y.Z")
        return 2
    base = f"https://raw.githubusercontent.com/betterleaks/betterleaks/{tag}/"
    got = {}
    for src in ("config/betterleaks.toml", "LICENSE"):
        with urllib.request.urlopen(base + src, timeout=60) as r:
            got[src] = r.read()
    try:
        data = convert(got["config/betterleaks.toml"].decode("utf-8"))
    except SyncError as exc:
        print(f"sync_betterleaks: {exc}", file=sys.stderr)
        return 1
    if "--check" in argv:
        print(f"Betterleaks {tag}: {len(data['rules'])} rules convert")
        return 0
    dst = Path(__file__).resolve().parent.parent / "maisecrets" / "rules"
    (dst / "betterleaks.toml").write_bytes(got["config/betterleaks.toml"])
    (dst / "LICENSE-betterleaks").write_bytes(got["LICENSE"])
    (dst / "BETTERLEAKS_VERSION").write_text(tag + "\n")
    (dst / "betterleaks.json").write_text(json.dumps({"version": tag, **data}, ensure_ascii=False, indent=0,
                                                     sort_keys=True) + "\n", encoding="utf-8")
    print(f"vendored Betterleaks {tag}: {len(data['rules'])} rules")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
