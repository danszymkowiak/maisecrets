"""The rule set as a value (TASK-27): explicit settings build an immutable rule set, and scan() takes one; without one
it uses the set built from the config, as before. No caller changes a module global to get other rules, so nothing
leaks from one test or bench arm into the next.

Run: python3 -m unittest tests.test_ruleset -v
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect  # noqa: E402

AHV = "756.9217.0769.85"        # the ZAS example


class RuleSetTests(unittest.TestCase):
    def test_a_rule_set_built_from_settings_is_used_by_scan_and_nothing_else_changes(self):
        swiss = detect.build(detect.Settings(regions=("generic", "ch"), languages=("en", "de", "fr", "it")))
        self.assertIn("ch-ahv", {r.id for r in swiss.rules})
        self.assertEqual([m.kind for m in detect.scan(f"AHV {AHV}", ruleset=swiss)], ["ch-ahv"])
        # the default set (the tests pin de_DE: region de) is not touched
        self.assertEqual([m.kind for m in detect.scan(f"AHV {AHV}")], [])
        self.assertNotIn("ch-ahv", {r.id for r in detect.rules()})

    def test_the_rule_set_is_immutable(self):
        rs = detect.build(detect.Settings())
        self.assertIsInstance(rs.rules, tuple)
        with self.assertRaises(Exception):
            rs.rules = ()

    def test_the_default_set_is_built_once(self):
        self.assertIs(detect.default_ruleset(), detect.default_ruleset())
        self.assertIs(detect.rules(), detect.default_ruleset().rules)

    def test_the_vendored_set_is_a_setting(self):
        bl = detect.build(detect.Settings(secret_rules="betterleaks"))
        self.assertIn("aikido-ci-token", {r.id for r in bl.rules})
        self.assertNotIn("aikido-ci-token", {r.id for r in detect.rules()})
        with self.assertRaises(ValueError):
            detect.build(detect.Settings(secret_rules="trufflehog"))

    def test_the_default_settings_come_from_the_config(self):
        s = detect.settings_from_config()
        a = detect.active_regions()
        self.assertEqual((s.regions, s.languages), (a.regions, a.languages))
        self.assertEqual((s.secret_rules, s.normalise), (detect.SECRET_RULES, detect.NORMALISE))


class NoGlobalAssignmentTests(unittest.TestCase):
    """The bench and the tests build a rule set; they never assign the detector's rule globals."""

    PATTERN = re.compile(r"\b(?:detect|_detect|D)\.(?:_RULES|NORMALISE|SECRET_RULES)\s*=(?!=)"
                         r"|setattr\(\s*(?:detect|_detect|D)\s*,\s*[\"'](?:_RULES|NORMALISE|SECRET_RULES)[\"']")

    def test_no_file_assigns_them(self):
        hits = []
        for folder in ("tests", "bench/maisecrets_bench", "bench/tests", "scripts"):
            for path in sorted((ROOT / folder).rglob("*.py")):
                if path.name == Path(__file__).name:
                    continue
                for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if self.PATTERN.search(line):
                        hits.append(f"{path.relative_to(ROOT)}:{n}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
