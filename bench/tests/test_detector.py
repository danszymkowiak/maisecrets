"""The bench imports the plugin's detector with a temp maisecrets home, never the real store (CLAUDE.md).

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from maisecrets_bench.adapters.plugin import detector


class DetectorTests(unittest.TestCase):
    def test_the_home_is_a_temp_dir_with_the_test_store(self):
        home = Path(os.environ["MAISECRETS_HOME"])
        self.assertNotEqual(home, Path.home() / ".maisecrets")
        self.assertIn('"jsonfile"', (home / "config.json").read_text(encoding="utf-8"))

    def test_the_known_types_cover_every_region(self):
        types = detector.known_types()
        for t in ("SECRET", "EMAIL", "PHONE", "IBAN", "CARD", "IP", "DE_TAX_ID", "US_SSN", "IT_FISCAL_CODE"):
            self.assertIn(t, types)
        self.assertNotIn("OUT_OF_SCOPE", types)


if __name__ == "__main__":
    unittest.main()
