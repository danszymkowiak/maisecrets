"""The Betterleaks sync (TASK-19.1): rule filters are expressions (CEL-style names in v1.9, Expr in v2.0); the sync
parses each into a JSON tree the detector evaluates, accepts both naming styles, drops the live checks, and fails
on anything it does not know, naming the rule. Nothing is fetched here: the tests feed TOML text."""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sync_betterleaks", ROOT / "scripts" / "sync_betterleaks.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

SECRET = ["index", ["var", "finding"], ["lit", "secret"]]


def parse(text: str):
    return sync.parse(text, "r1")


class ParseTests(unittest.TestCase):
    def test_a_comparison_of_a_function_of_the_secret(self):
        self.assertEqual(parse('entropy(finding["secret"]) <= 3.8'),
                         ["bin", "<=", ["call", "entropy", [SECRET]], ["lit", 3.8]])

    def test_the_v19_names_become_the_v2_names(self):
        self.assertEqual(parse('filter.entropy(finding["secret"]) < 3.5 '
                               '|| filter.tokenRatio(finding["secret"]) >= 2.5'),
                         parse('entropy(finding["secret"]) < 3.5 || tokenRatio(finding["secret"]) >= 2.5'))

    def test_and_binds_tighter_than_or_and_word_operators_are_the_same(self):
        self.assertEqual(parse("a || b && c"), ["bin", "||", ["var", "a"], ["bin", "&&", ["var", "b"], ["var", "c"]]])
        self.assertEqual(parse("a or b and c"), parse("a || b && c"))
        self.assertEqual(parse("not a"), parse("!a"))

    def test_lists_raw_strings_and_trailing_commas(self):
        self.assertEqual(parse('matchesAny(finding["secret"], [`^a\\d$`, "b\\n",],)'),
                         ["call", "matchesAny", [SECRET, ["list", [["lit", "^a\\d$"], ["lit", "b\n"]]]]])

    def test_let_bindings_comments_slices_and_a_ternary(self):
        tree = parse('// a comment\nlet raw = finding["fragment_raw"];\n'
                     'let pre = raw[max(finding["match_start_idx"] - 50, 0):];\n'
                     'let level = len(pre) > 3 ? "medium" : "low";\nlower(pre) contains "client"')
        self.assertEqual(tree[0], "let")
        self.assertEqual(tree[1], "raw")
        inner = tree[3]
        self.assertEqual(inner[2][0], "slice")
        self.assertIsNone(inner[2][3], "an open upper bound")
        self.assertEqual(inner[3][2][0], "cond")
        self.assertEqual(inner[3][3], ["bin", "contains", ["call", "lower", [["var", "pre"]]], ["lit", "client"]])

    def test_in_and_arithmetic(self):
        self.assertEqual(parse('x in ["a", "b"]'), ["bin", "in", ["var", "x"], ["list", [["lit", "a"], ["lit", "b"]]]])
        self.assertEqual(parse("a + b * 2 - 1"),
                         ["bin", "-", ["bin", "+", ["var", "a"], ["bin", "*", ["var", "b"], ["lit", 2]]], ["lit", 1]])

    def test_an_unknown_function_names_the_rule(self):
        with self.assertRaisesRegex(sync.SyncError, "r1.*'launch'"):
            parse('launch(finding["secret"])')

    def test_unknown_syntax_names_the_rule(self):
        with self.assertRaisesRegex(sync.SyncError, "r1"):
            parse('entropy(finding["secret"]) <=> 3')


TOML = '''
title = "t"
prefilter = 'matchesAny(attributes["path"], [`\\.png$`])'
filter = 'matchesAny(finding["secret"], [`^true$`])'

[[rules]]
id = "demo-token"
description = "Demo"
regex = 'demo_[a-z0-9]{20}'
keywords = ["demo_"]
confidence = "high"
filter = 'filter.entropy(finding["secret"]) < 3'
validate = 'http.get("https://example.invalid")'
analyze = 'x'
revoke = 'y'
skipReport = true
secretGroup = 1
'''


class ConvertTests(unittest.TestCase):
    def test_a_rule_keeps_its_fields_and_loses_the_live_checks(self):
        out = sync.convert(TOML)
        (r,) = out["rules"]
        self.assertEqual(r["id"], "demo-token")
        self.assertEqual(r["filter"], parse('entropy(finding["secret"]) < 3'))
        self.assertEqual((r["confidence"], r["skipReport"], r["secretGroup"]), ("high", True, 1))
        for gone in ("validate", "analyze", "revoke"):
            self.assertNotIn(gone, r)
        self.assertEqual(out["filter"][0], "call")
        self.assertEqual(out["prefilter"][1], "matchesAny")

    def test_value_group_is_the_v2_name_of_secret_group(self):
        r = sync.convert(TOML.replace("secretGroup = 1", "valueGroup = 2"))["rules"][0]
        self.assertEqual(r["secretGroup"], 2)

    def test_a_rule_whose_filter_fails_stops_the_sync(self):
        with self.assertRaisesRegex(sync.SyncError, "demo-token"):
            sync.convert(TOML.replace("filter.entropy(", "filter.rocket("))

    def test_an_unknown_rule_field_stops_the_sync(self):
        with self.assertRaisesRegex(sync.SyncError, "demo-token.*'colour'"):
            sync.convert(TOML.replace("skipReport = true", "skipReport = true\ncolour = 'red'"))


if __name__ == "__main__":
    unittest.main()
