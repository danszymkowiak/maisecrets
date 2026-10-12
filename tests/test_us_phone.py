"""A US phone number in the (NXX) NXX-XXXX form (TASK-23): region `us` finds it in prose; the North American numbering
plan bounds the shape (area code and exchange start with 2-9, an area code's middle digit is not 9: reserved).

Run: python3 -m unittest tests.test_us_phone -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect  # noqa: E402


class UsPhoneTests(unittest.TestCase):
    def use(self, *region: str):
        self.rs = detect.build(detect.Settings(regions=("generic", *region), languages=("en",)))

    def phones(self, text: str) -> list[str]:
        return [m.value for m in detect.scan(text, ruleset=self.rs) if m.type == "PHONE"]

    def test_the_parenthesised_form_is_found_in_prose(self):
        self.use("us")
        for text, want in (("Questions: (484) 360-7563", "(484) 360-7563"),
                           ("Acme Corp, (212) 555-0147, New York", "(212) 555-0147"),
                           ("call (312)555-0198 today", "(312)555-0198"),
                           ("Tel. (415) 867-5309.", "(415) 867-5309")):
            with self.subTest(text=text):
                self.assertEqual(self.phones(text), [want])

    def test_shapes_outside_the_numbering_plan_are_no_hit(self):
        self.use("us")
        for text in ("(123) 456-7890", "(212) 055-0147", "(212) 155-0147", "(092) 555-0147", "(494) 360-7563",
                     "f(494) 360-7563", "(494) 360-75631", "x(494) 360-7563"):
            with self.subTest(text=text):
                self.assertEqual(self.phones(text), [])

    def test_without_region_us_the_rule_does_not_run(self):
        self.use("de")
        self.assertEqual(self.phones("Questions: (484) 360-7563"), [])


if __name__ == "__main__":
    unittest.main()
