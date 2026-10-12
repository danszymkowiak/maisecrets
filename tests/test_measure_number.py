"""A number after a measure label is no password (the measure-number fix), also at the end of a sentence (TASK-32):
`... TOKEN_TTL = <seconds>.` was a hit because the check saw the full stop as part of the value. A real value after a
password label keeps its hit with a full stop after it.

Run: python3 -m unittest tests.test_measure_number -v
"""
from __future__ import annotations

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

from maisecrets import detect  # noqa: E402

_R = random.Random(32)


def secrets(text: str) -> list[str]:
    return [m.value for m in detect.scan(text) if m.type == "SECRET"]


class MeasureNumberTests(unittest.TestCase):
    def test_a_measure_number_at_the_end_of_a_sentence_is_no_hit(self):
        for label in ("TOKEN_TTL", "REFRESH_TOKEN_MAX_AGE", "SECRET_ROTATION_DAYS"):
            seconds = str(_R.randrange(100000, 9999999))
            for text in (f"Set {label} = {seconds}.", f"{label} = {seconds}", f"{label} = {seconds}.\nNext line"):
                with self.subTest(text=text):
                    self.assertEqual(secrets(text), [])

    def test_a_password_before_a_full_stop_is_still_a_hit(self):
        value = "".join(_R.choice(string.ascii_letters + string.digits) for _ in range(14)) + "7Qx"
        found = secrets(f"DB_PASSWORD = {value}.")
        self.assertTrue(found and found[0].startswith(value), found)


if __name__ == "__main__":
    unittest.main()
