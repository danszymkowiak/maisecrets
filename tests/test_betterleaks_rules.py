"""Betterleaks rules in the detector (TASK-19.2): the evaluator of the converted rule filters (filterexpr.py),
the switch between the vendored gitleaks and Betterleaks sets, and the per-rule fixes of vendored rules, which sit in
rules/overrides.txt keyed by the upstream rule ID.

Run: python3 -m unittest tests.test_betterleaks_rules -v
Every token is generated at run time, so no literal sits in the tree.
"""
from __future__ import annotations

import json
import os
import random
import string
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect, filterexpr  # noqa: E402

_spec_path = ROOT / "scripts" / "sync_betterleaks.py"
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("sync_betterleaks", _spec_path)
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

AN = string.ascii_letters + string.digits
_R = random.Random(19)


def rnd(n: int, alphabet: str = AN) -> str:
    return "".join(_R.choice(alphabet) for _ in range(n))


def finding(secret: str, text: str | None = None) -> dict:
    text = secret if text is None else text
    a = text.find(secret)
    return filterexpr.finding(text, a, a + len(secret), secret)


def drops(expr: str, secret: str, text: str | None = None) -> bool:
    return filterexpr.discards(sync.parse(expr, "t"), finding(secret, text))


class EvaluatorTests(unittest.TestCase):
    def test_entropy_and_a_comparison(self):
        self.assertTrue(drops('entropy(finding["secret"]) <= 3.0', "aaaabbbb"))
        self.assertFalse(drops('entropy(finding["secret"]) <= 3.0', rnd(32)))

    def test_matches_any_takes_re2_patterns_and_contains_any_substrings(self):
        self.assertTrue(drops('matchesAny(finding["secret"], [`.+EXAMPLE$`])', "AKIAEXAMPLE"))
        self.assertTrue(drops(r'matchesAny(finding["secret"], [`^(?i:a+|b+)$`])', "AAAA"))
        self.assertTrue(drops('containsAny(finding["secret"], ["xyz", "abc"])', "1abc2"))
        self.assertFalse(drops('containsAny(finding["secret"], ["xyz"])', "1abc2"))

    def test_let_slices_find_match_and_the_line_around_the_match(self):
        text = "x = my_token." + (s := rnd(24))
        expr = ('let pre = findMatch(finding["fragment_raw"][max(finding["match_start_idx"] - 50, '
                'finding["match_line_start_idx"]):finding["match_start_idx"]], `[\\w.-]{0,50}$`);'
                'let l = pre == "" ? "none" : "some"; l == "none"')
        self.assertFalse(drops(expr, s, text), "the word glued to the value is found: not none")
        self.assertTrue(drops(expr, s, "x = " + s), "a space before the value: nothing glued")
        self.assertTrue(drops('finding["line"] contains "my_token"', s, "a\n" + text + "\nb"))
        self.assertFalse(drops('finding["line"] contains "a"', s, "a\n" + text + "\nb"))

    def test_split_join_len_and_negative_arithmetic(self):
        text = "a\nb\nc\n" + (s := rnd(20))
        expr = ('let before = split(finding["fragment_raw"][0:finding["match_start_idx"]], "\\n");'
                'len(before) == 4 && join(before[0:2], "-") == "a-b" && before[len(before) - 1] == ""')
        self.assertTrue(drops(expr, s, text))

    def test_token_ratio_is_unknown_and_never_discards(self):
        # no stdlib tokenizer (TASK-19.3 decides): the clause falls away and the entropy limit stays
        expr = 'entropy(finding["secret"]) < 3.0 || tokenRatio(finding["secret"]) >= 2.5'
        self.assertFalse(drops(expr, rnd(32)))
        self.assertTrue(drops(expr, "aaaabbbb"))
        self.assertFalse(drops('failsTokenEfficiency(finding["secret"])', "hello world"))

    def test_set_confidence_returns_nothing_that_discards(self):
        self.assertFalse(drops('let _ = setConfidence("medium"); false', "x"))

    def test_a_filter_that_errors_keeps_the_finding(self):
        # a redaction tool keeps a hit it cannot judge
        self.assertFalse(drops('len(finding["secret"]) + "x" == 1', rnd(10)))
        self.assertFalse(drops('finding["nothing"]["deeper"] == "x"', rnd(10)))

    def test_word_operators_and_in(self):
        self.assertTrue(drops('finding["secret"] in ["a", "b"] or not true', "a"))
        self.assertTrue(drops('finding["secret"] startsWith "ab" and finding["secret"] endsWith "yz"', "abxyz"))
        self.assertTrue(drops('finding["secret"] matches "^[a-z]+$"', "abc"))


class SwitchTests(unittest.TestCase):
    def setUp(self):
        self.saved = (detect.SECRET_RULES, detect._RULES)
        self.addCleanup(self.restore)

    def restore(self):
        detect.SECRET_RULES, detect._RULES = self.saved

    def use(self, name: str):
        detect.SECRET_RULES, detect._RULES = name, None

    def ids(self) -> set:
        return {r.id for r in detect.rules()}

    def test_off_loads_gitleaks_and_no_betterleaks_rule(self):
        self.use("gitleaks")
        g = {r["id"] for r in json.loads((detect.RULES_DIR / "gitleaks.json").read_text(encoding="utf-8"))["rules"]
             if "regex" in r}
        self.assertLessEqual(g, self.ids())
        self.assertNotIn("aikido-ci-token", self.ids())   # a Betterleaks-only rule, the premise below

    def test_on_loads_betterleaks_without_its_component_only_rules(self):
        self.use("betterleaks")
        bl = json.loads((detect.RULES_DIR / "betterleaks.json").read_text(encoding="utf-8"))["rules"]
        reported = {r["id"] for r in bl if "regex" in r and not r.get("skipReport")}
        self.assertLessEqual(reported, self.ids())
        self.assertNotIn("aws-secret-access-key", self.ids(), "skipReport: only a component of aws-access-token")
        self.assertTrue(any(r.filter for r in detect.rules() if r.id == "aws-access-token"))

    def test_an_unknown_name_fails_loudly(self):
        self.use("trufflehog")
        with self.assertRaises(ValueError):
            detect.rules()

    def test_a_token_is_found_and_the_rule_filter_drops_a_placeholder(self):
        self.use("betterleaks")
        kid = "AKIA" + rnd(16, string.ascii_uppercase + "234567")
        self.assertIn(("aws-access-token", kid), [(m.kind, m.value) for m in detect.scan(f"id {kid} here")])
        # the vendored filter: `.+EXAMPLE$` is AWS's documented example key
        ex = "AKIA" + rnd(9, string.ascii_uppercase + "234567") + "EXAMPLE"
        self.assertNotIn("aws-access-token", [m.kind for m in detect.scan(f"id {ex} here")])

    def test_the_global_filter_drops_a_template(self):
        self.use("betterleaks")
        bl = json.loads((detect.RULES_DIR / "betterleaks.json").read_text(encoding="utf-8"))
        self.assertTrue(filterexpr.discards(bl["filter"], finding("${API_TOKEN}")))
        self.assertFalse(filterexpr.discards(bl["filter"], finding(rnd(30))))


class OverrideTests(unittest.TestCase):
    def test_every_override_names_a_vendored_rule_and_a_known_fix(self):
        self.assertEqual(detect.override_problems(), [])

    def test_an_override_for_a_rule_upstream_dropped_is_refused(self):
        lines = (detect.RULES_DIR / "overrides.txt").read_text(encoding="utf-8") + "\nno-such-rule  ds-value\n"
        self.assertIn("overrides.txt: no-such-rule is in no vendored rule set", detect.override_problems(lines))

    def test_an_override_naming_an_unknown_fix_is_refused(self):
        lines = "generic-api-key  rocket\n"
        self.assertIn("overrides.txt: generic-api-key names an unknown fix 'rocket'", detect.override_problems(lines))

    def test_the_four_fixed_rules_carry_their_fixes_in_both_sets(self):
        saved = (detect.SECRET_RULES, detect._RULES)
        self.addCleanup(lambda: (setattr(detect, "SECRET_RULES", saved[0]), setattr(detect, "_RULES", saved[1])))
        for name in ("gitleaks", "betterleaks"):
            detect.SECRET_RULES, detect._RULES = name, None
            fixes = {r.id: r.fixes for r in detect.rules()}
            for rid in ("generic-api-key", "curl-auth-user", "aws-access-token", "hashicorp-tf-password"):
                with self.subTest(name=name, rule=rid):
                    self.assertTrue(fixes[rid])

    def test_the_fixes_still_apply_with_betterleaks(self):
        saved = (detect.SECRET_RULES, detect._RULES)
        self.addCleanup(lambda: (setattr(detect, "SECRET_RULES", saved[0]), setattr(detect, "_RULES", saved[1])))
        detect.SECRET_RULES, detect._RULES = "betterleaks", None
        kid = "AKIA" + rnd(16, string.ascii_uppercase + "234567")
        scope = f"{kid}/20261008/eu-central-1/s3/aws4_request"
        self.assertEqual([m.kind for m in detect.scan(f"Authorization: AWS4-HMAC-SHA256 Credential={scope}")], [])
        self.assertEqual([m.kind for m in detect.scan('tz_key = "Europe/Dublin"\n')], [])


if __name__ == "__main__":
    unittest.main()
