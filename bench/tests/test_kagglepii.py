"""The Learning Agency Lab's PII Data Detection competition (TASK-11.36): student essays as tokens with whitespace flags
and BIO labels. The adapter rebuilds the text and turns label runs into character spans. The records here are made
up in the competition's format; the real data needs the user's Kaggle account and stays out of the repository.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench.adapters import kagglepii
from maisecrets_bench.labels import load
from maisecrets_bench.schema import OUT_OF_SCOPE


def record(doc, words, labels):
    return {"document": doc, "tokens": [w for w, _ in words], "trailing_whitespace": [ws for _, ws in words],
            "labels": labels, "full_text": "".join(w + (" " if ws else "") for w, ws in words)}


R = record(7, [("Reflection", True), ("by", True), ("Anna", True), ("Muster", False), (",", True), ("mail", True),
               ("anna@example.org", True), ("or", True), ("555", True), ("0100", False), (".", False)],
           ["O", "O", "B-NAME_STUDENT", "I-NAME_STUDENT", "O", "O", "B-EMAIL", "O", "B-PHONE_NUM", "I-PHONE_NUM",
            "O"])


class AdapterTests(unittest.TestCase):
    def test_label_runs_become_character_spans_of_the_rebuilt_text(self):
        (s,) = list(kagglepii.samples([R], load("kagglepii")))
        self.assertEqual(s.text, R["full_text"])
        got = [(s.text[sp.start:sp.end], sp.label, sp.maisecrets_type, sp.gold) for sp in s.spans]
        self.assertEqual(got, [("Anna Muster", "NAME_STUDENT", OUT_OF_SCOPE, "pos"),
                               ("anna@example.org", "EMAIL", "EMAIL", "pos"),
                               ("555 0100", "PHONE_NUM", "PHONE", "pos")])
        self.assertEqual((s.dataset, s.language, s.sample_id), ("kagglepii", "en", "7"))

    def test_two_names_side_by_side_stay_two_spans(self):
        r = record(8, [("Anna", True), ("Bob", False)], ["B-NAME_STUDENT", "B-NAME_STUDENT"])
        (s,) = list(kagglepii.samples([r], load("kagglepii")))
        self.assertEqual([s.text[sp.start:sp.end] for sp in s.spans], ["Anna", "Bob"])

    def test_a_text_that_does_not_match_its_tokens_is_dropped_and_counted(self):
        bad = dict(R, full_text=R["full_text"] + "x")
        stats = kagglepii.Stats()
        self.assertEqual(list(kagglepii.samples([bad], load("kagglepii"), stats)), [])
        self.assertEqual(stats.dropped, 1)

    def test_every_competition_label_has_a_type(self):
        table = load("kagglepii")
        for label in kagglepii.LABELS:
            table.type_of(label)        # raises for a label the table lacks


class TokenTests(unittest.TestCase):
    def test_the_token_is_read_from_the_environment_or_the_env_file_and_never_shown(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest import mock
        with mock.patch.dict(os.environ, {"KAGGLE_API_TOKEN": "from-env"}):
            self.assertEqual(kagglepii.token(Path("/nonexistent")), "from-env")
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=True):
            (Path(d) / ".env").write_text("OTHER=1\nexport KAGGLE_API_TOKEN='from-file'\n", encoding="utf-8")
            self.assertEqual(kagglepii.token(Path(d)), "from-file")
            (Path(d) / ".env").write_text("OTHER=1\n", encoding="utf-8")
            with self.assertRaises(Exception) as ctx:
                kagglepii.token(Path(d))
            self.assertIn("KAGGLE_API_TOKEN", str(ctx.exception))



class LicenceTests(unittest.TestCase):
    def test_piilo_is_cc_by_with_attribution_not_local_only(self):
        # PIILO, the competition's data: "PIILO © 2024 by The Learning Agency Lab is licensed under CC BY 4.0"
        # (the-learning-agency-lab.com/learning-exchange/piilo-dataset/, user 2026-10-13)
        from maisecrets_bench import run
        self.assertNotIn("kagglepii", run.LOCAL_ONLY)
        self.assertIn("CC BY 4.0", run.ATTRIBUTION["kagglepii"])
        self.assertIn("The Learning Agency Lab", run.ATTRIBUTION["kagglepii"])

if __name__ == "__main__":
    unittest.main()
