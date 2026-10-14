"""The vote and the review gate (TASK-34.5): rule hits redact; model spans redact when every model agrees, and go to a
person otherwise; nothing is released while a review is open; a review file applied by a second run gives the same
output as the same answers given at a terminal.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact import app, review  # noqa: E402
from maisecrets_redact.pipeline import Document, Span  # noqa: E402

TEXT = "Kunde Max Muster, wohnhaft Bahnhofstrasse 12, IBAN CH93 0076 2011 6238 5295 7."


def fake(name: str, words: dict[str, str]):
    def find(doc: Document):
        out = []
        for w, t in words.items():
            at = doc.text.find(w)
            if at >= 0:
                out.append(Span(at, at + len(w), t, name, 0.8))
        return out
    return find


M1 = fake("m1", {"Max Muster": "NAME", "Bahnhofstrasse 12": "ADDRESS"})
M2 = fake("m2", {"Max Muster": "NAME", "Muster": "NAME"})          # agrees on the name, misses the address


class DecideTests(unittest.TestCase):
    def test_unanimous_redacts_and_split_goes_to_review(self):
        doc = Document("t.txt", TEXT)
        d = review.decide(doc, rule_spans=[], model_spans={"m1": M1(doc), "m2": M2(doc)})
        self.assertEqual([doc.text[s.start:s.end] for s in d.redact], ["Max Muster"])
        self.assertEqual([doc.text[s.start:s.end] for s in d.review], ["Bahnhofstrasse 12"])

    def test_rule_hits_always_redact_and_cover_model_spans(self):
        doc = Document("t.txt", TEXT)
        iban = TEXT.index("CH93")
        rule = Span(iban, iban + len("CH93 0076 2011 6238 5295 7"), "IBAN", "rules")
        inside = Span(iban, iban + 4, "ACCOUNT", "m1")
        d = review.decide(doc, rule_spans=[rule], model_spans={"m1": [inside], "m2": []})
        self.assertEqual(d.redact, (rule,))
        self.assertEqual(d.review, ())

    def test_k_of_n_redacts_what_k_models_found_and_reviews_the_rest(self):
        # the default vote (user, 2026-10-12): two of the four models agree
        doc = Document("x.txt", "Erika Muster wohnt in Bern, Hans Meier auch")
        spans = {"a": [Span(0, 12, "NAME", "a"), Span(22, 26, "ADDRESS", "a")], "b": [Span(0, 12, "NAME", "b")],
                 "c": [Span(28, 38, "NAME", "c")], "d": []}
        d = review.decide(doc, [], spans, k=2)
        self.assertEqual([(s.start, s.end) for s in d.redact], [(0, 12)])
        self.assertEqual([(s.start, s.end) for s in d.review], [(22, 26), (28, 38)])

    def test_a_span_only_an_unreviewed_model_found_is_dropped_not_asked(self):
        doc = Document("x.txt", "Erika Muster wohnt in Bern, Hans Meier auch")
        spans = {"a": [Span(0, 12, "NAME", "a")], "pf": [Span(0, 12, "NAME", "pf"), Span(28, 38, "NAME", "pf")],
                 "c": [Span(22, 26, "ADDRESS", "c")]}
        d = review.decide(doc, [], spans, k=2, not_reviewed=("pf",))
        self.assertEqual([(s.start, s.end) for s in d.redact], [(0, 12)])
        self.assertEqual([(s.start, s.end) for s in d.review], [(22, 26)], "pf's lone span is dropped, c's is asked")

    def test_the_defaults_are_two_of_four_without_privacy_filter_reviews(self):
        from maisecrets_redact import models
        self.assertEqual(len(models.DEFAULTS), 4)
        self.assertEqual((models.VOTE_K, models.NOT_REVIEWED), (2, ("openai/privacy-filter",)))

    def test_the_command_runs_the_default_vote(self):
        from unittest import mock
        from maisecrets_redact import cli, models
        d = Path(tempfile.mkdtemp())
        (d / "a.txt").write_text("x\n", encoding="utf-8")
        with mock.patch.object(cli, "_model_detectors", return_value={"m": lambda doc: []}), \
                mock.patch.object(app, "run_file", return_value=app.Result("written")) as run:
            cli.main([str(d / "a.txt")])
        kw = run.call_args.kwargs
        self.assertEqual((kw["vote_k"], kw["not_reviewed"]), (models.VOTE_K, models.NOT_REVIEWED))

    def test_without_models_only_the_rules_decide(self):
        doc = Document("t.txt", TEXT)
        d = review.decide(doc, rule_spans=[], model_spans={})
        self.assertEqual((d.redact, d.review), ((), ()))


class TableTests(unittest.TestCase):
    """A CSV through run_file (TASK-49): a model's name across two cells redacts each cell, so the row keeps its
    columns, and a city a model calls an email stays."""

    def test_the_row_keeps_its_columns_and_the_city(self):
        d = Path(tempfile.mkdtemp())
        src, out = d / "people.csv", d / "people.csv.redacted.csv"
        src.write_text("first,last,city\nMax,Muster,Zurich\n", encoding="utf-8")
        words = {"Max\tMuster": "NAME", "Zurich": "EMAIL"}
        result = app.run_file(src, out, model_detectors={"m1": fake("m1", words), "m2": fake("m2", words)},
                              regions=("generic",), interactive=False)
        self.assertEqual(result.status, "written")
        row = list(csv.reader(io.StringIO(out.read_text(encoding="utf-8"), newline="")))[1]
        self.assertEqual(len(row), 3, row)
        self.assertNotIn("Max", row[0])
        self.assertNotIn("Muster", row[1])
        self.assertEqual(row[2], "Zurich")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.src = self.dir / "kunde.txt"
        self.src.write_text(TEXT, encoding="utf-8")
        self.out = self.dir / "kunde.txt.redacted.txt"

    def run_file(self, **kw):
        return app.run_file(self.src, self.out, model_detectors={"m1": M1, "m2": M2}, regions=("generic",), **kw)

    def test_an_open_review_writes_no_output_and_a_review_file(self):
        result = self.run_file(interactive=False)
        self.assertEqual(result.status, "review")
        self.assertFalse(self.out.exists())
        items = json.loads(self.out.with_name(self.out.name + ".review.json").read_text(encoding="utf-8"))["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0]["type"], items[0]["decision"]), ("ADDRESS", None))
        self.assertNotIn("Bahnhofstrasse 12", json.dumps(items), "the value is masked in the review file")

    def test_the_review_file_gives_the_same_output_as_the_terminal(self):
        self.run_file(interactive=False)
        rf = self.out.with_name(self.out.name + ".review.json")
        data = json.loads(rf.read_text(encoding="utf-8"))
        data["items"][0]["decision"] = "redact"
        rf.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_file(interactive=False).status, "written")
        from_file = self.out.read_text(encoding="utf-8")
        self.out.unlink()
        rf.unlink()
        self.assertEqual(self.run_file(interactive=True, ask=lambda item: "redact").status, "written")
        self.assertEqual(self.out.read_text(encoding="utf-8"), from_file)
        self.assertNotIn("Bahnhofstrasse 12", from_file)
        self.assertNotIn("Max Muster", from_file)
        self.assertIn("CH93", TEXT)
        self.assertNotIn("CH93", from_file)

    def test_keep_leaves_the_span(self):
        self.run_file(interactive=True, ask=lambda item: "keep")
        self.assertIn("Bahnhofstrasse 12", self.out.read_text(encoding="utf-8"))

    def test_no_review_redacts_every_disputed_span(self):
        self.assertEqual(self.run_file(interactive=False, no_review=True).status, "written")
        self.assertNotIn("Bahnhofstrasse 12", self.out.read_text(encoding="utf-8"))

    def test_a_stale_review_file_is_refused(self):
        self.run_file(interactive=False)
        self.src.write_text(TEXT.replace("Bahnhofstrasse 12", "Seestrasse 99a"), encoding="utf-8")
        with self.assertRaisesRegex(review.StaleReview, "changed"):
            self.run_file(interactive=False)


if __name__ == "__main__":
    unittest.main()
