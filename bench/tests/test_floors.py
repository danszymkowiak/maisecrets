"""The floor table (bench/floors.toml, TASK-21.7): tiers of recall floors per type, the dataset weights of the
false-positive objective, and SECRET split into prefixed tokens and generic credentials for scoring.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

from maisecrets_bench import floors
from maisecrets_bench.labels import TABLES
from maisecrets_bench.paths import BenchError


def _load_text(text: str) -> floors.Floors:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "floors.toml"
        p.write_text(text, encoding="utf-8")
        return floors.load(p)


MINI = """
default_tier = "default"
[tiers.critical]
floor = 0.999
types = ["IBAN", "SECRET_PREFIXED"]
[tiers.default]
floor = "no_regression"
types = ["SECRET_GENERIC"]
[weights]
gretel = 2.0
[secret]
prefixed_parts = ["Github Classic Token"]
prefixed_labels = ["synthetic:GITHUB"]
"""


class FloorTests(unittest.TestCase):
    def test_the_repository_table_loads_and_names_the_users_tiers(self):
        f = floors.load()
        self.assertEqual(f.tier_of("IBAN"), ("critical", 0.999))
        self.assertEqual(f.tier_of("CARD"), ("critical", 0.999))
        self.assertEqual(f.tier_of("EMAIL"), ("high", 0.99))
        self.assertEqual(f.tier_of("SECRET_PREFIXED"), ("critical", 0.999))
        self.assertEqual(f.tier_of("SECRET_GENERIC"), ("default", "no_regression"))
        self.assertEqual(f.tier_of("UK_POSTCODE"), ("default", "no_regression"), "an unlisted type")

    def test_an_unknown_type_in_a_tier_fails(self):
        with self.assertRaisesRegex(BenchError, "'NOT_A_TYPE'"):
            _load_text(MINI.replace('"IBAN"', '"NOT_A_TYPE"'))

    def test_secret_itself_cannot_sit_in_a_tier(self):
        with self.assertRaisesRegex(BenchError, "SECRET"):
            _load_text(MINI.replace('"IBAN"', '"SECRET"'))

    def test_a_type_in_two_tiers_fails(self):
        with self.assertRaisesRegex(BenchError, "'IBAN'"):
            _load_text(MINI.replace('types = ["SECRET_GENERIC"]', 'types = ["SECRET_GENERIC", "IBAN"]'))

    def test_weights_default_to_one(self):
        f = _load_text(MINI)
        self.assertEqual((f.weight("gretel"), f.weight("creddata")), (2.0, 1.0))

    def test_secret_splits_by_creddata_category_and_by_label(self):
        f = _load_text(MINI)
        self.assertEqual(f.scoring_type("creddata", "Github Classic Token", "SECRET"), "SECRET_PREFIXED")
        self.assertEqual(f.scoring_type("creddata", "API:Key:Github Classic Token", "SECRET"), "SECRET_PREFIXED")
        self.assertEqual(f.scoring_type("creddata", "Password", "SECRET"), "SECRET_GENERIC")
        self.assertEqual(f.scoring_type("synthetic", "GITHUB", "SECRET"), "SECRET_PREFIXED")
        self.assertEqual(f.scoring_type("gretel", "password", "SECRET"), "SECRET_GENERIC")
        self.assertEqual(f.scoring_type("gretel", "iban", "IBAN"), "IBAN")

    def test_every_type_of_every_label_table_resolves_to_a_tier(self):
        f = floors.load()
        for path in sorted(TABLES.glob("*.toml")):
            dataset = path.stem
            for label, t in tomllib.loads(path.read_text(encoding="utf-8"))["labels"].items():
                if t == "OUT_OF_SCOPE":
                    continue
                tier, _ = f.tier_of(f.scoring_type(dataset, label, t))
                self.assertIn(tier, ("critical", "high", "default", "none"), (dataset, label))

    def test_every_prefixed_part_is_a_creddata_category_part(self):
        f = floors.load()
        parts = {p for k in tomllib.loads((TABLES / "creddata.toml").read_text(encoding="utf-8"))["labels"]
                 for p in k.split(":")}
        self.assertLessEqual(f.prefixed_parts, parts)
        self.assertGreater(len(f.prefixed_parts), 20)


if __name__ == "__main__":
    unittest.main()
