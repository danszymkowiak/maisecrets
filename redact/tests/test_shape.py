"""A password with no context (TASK-55, user 2026-10-14): in a password manager's notes column or in plain text no
rule, header or model finds it. Entropy does not either (human passwords score low, GUIDs and hashes high), so a
password-shape check: one token of 8 to 64 characters with three character classes that is no ID shape, no word and
digits, no code and no markup. A hit is a review item, never a redaction of its own. All values are synthetic.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact import app, extract, pipeline, review  # noqa: E402
from maisecrets_redact.pipeline import Document, Position, Span  # noqa: E402

# built here, not written out: the tree's own secret scan reads every literal
HITS = ["Xk8#" + "pLq2", "Tr0ub4" + "dor&3", "S0mmer!" + "2024", "Summer@" + "2024.", "Summer2024" + "!",
        "(Pa55" + "word!)", "qW3$" + "rty99"]


class ShapeTests(unittest.TestCase):
    def test_password_shapes(self):
        for t in HITS:
            self.assertTrue(pipeline.password_shaped(t), t)

    def test_id_shapes_are_not(self):
        for t in ("3c05ac01-0000-4000-8000-00000000c0de", "d41d8cd98f00b204e9800998ecf8427e", "2024-03-14T10:00Z",
                  "1710000000001", "v2.3.1-beta", "CHF1'200.50", "COVID-19", "ISO-9001", "#INV12345", "2024-Q1-05",
                  "AB-12-C", "192.168.0.1", "fe80::1ff:fe23:4567:890a", "user_id2", "TAG:4200", "amount=12.50"):
            self.assertFalse(pipeline.password_shaped(t), t)

    def test_words_with_digits_or_punctuation_are_not(self):
        for t in ("Version2024", "iPhone15", "Summer-2024", "McDonald's", "Jean-Pierre", "l'Économie", "Hello,World",
                  "Congratulations!", "„Wirtschaft“", "Account(s)", "**Important**", "#MondayMotivation"):
            self.assertFalse(pipeline.password_shaped(t), t)

    def test_urls_mail_paths_markup_and_placeholders_are_not(self):
        for t in ("https://login.example.com/a?b=1", "www.example.com/Path1", "max12@mailbox-test.de", "name12@host",
                  "C:\\Users\\Max1\\x", "/home/max/File1.txt", 'id="A-12"', "<b:Tag1>", "[Link](#a-b)",
                  "|Cell1|", "⟦SECRET_1⟧", "tmax.mustermann@mailbox-test.de", "short1!", "a" * 70 + "B1!"):
            self.assertFalse(pipeline.password_shaped(t), t)


def csv(header: str, row: str) -> Document:
    path = Path(tempfile.mkdtemp()) / "t.csv"
    path.write_text(header + "\n" + row + "\n", encoding="utf-8")
    return extract.extract(path)


class ScopeTests(unittest.TestCase):
    def test_a_notes_column_and_plain_text_are_checked(self):
        doc = csv("name,notes,city", f"Example,old pw {HITS[0]} for the router,{HITS[1]}")
        self.assertEqual([(doc.text[s.start:s.end], s.type, s.source) for s in pipeline.shape_spans(doc)],
                         [(HITS[0], "SECRET", "password-shape")])
        text = f"Wifi at the cabin: {HITS[2]} (ask Max)\n"
        plain = Document("t.txt", text, (Position(0, len(text), "file"),))
        self.assertEqual([text[s.start:s.end] for s in pipeline.shape_spans(plain)], [HITS[2]])

    def test_other_columns_and_structured_fields_are_not(self):
        doc = csv("comment_count,password_hint,url", f"{HITS[0]},{HITS[1]},{HITS[2]}")
        self.assertEqual(pipeline.shape_spans(doc), [])


class ReviewOnlyTests(unittest.TestCase):
    def test_a_hit_goes_to_review_and_is_never_redacted_alone(self):
        doc = Document("t.txt", f"pw {HITS[0]}")
        shape = [Span(3, 3 + len(HITS[0]), "SECRET", "password-shape")]
        d = review.decide(doc, [], {}, extra_review=shape)
        self.assertEqual((d.redact, d.review), ((), tuple(shape)))
        rule = Span(3, 3 + len(HITS[0]), "SECRET", "rules")
        self.assertEqual(review.decide(doc, [rule], {}, extra_review=shape).review, (), "a rule hit holds it already")

    def test_through_run_file_it_is_a_review_item(self):
        d = Path(tempfile.mkdtemp())
        src = d / "vault.csv"
        src.write_text(f"name,notes\nRouter,admin pw {HITS[1]}\n", encoding="utf-8")
        target = d / app.output_name(src)
        result = app.run_file(src, target, model_detectors={}, regions=("generic",), interactive=False)
        self.assertEqual((result.status, result.open_items), ("review", 1))
        items = json.loads(target.with_name(target.name + ".review.json").read_text(encoding="utf-8"))["items"]
        self.assertEqual((items[0]["type"], items[0]["where"]), ("SECRET", "row 2, column notes"))
        self.assertNotIn(HITS[1], json.dumps(items))
        self.assertEqual(app.run_file(src, target, model_detectors={}, regions=("generic",), interactive=True,
                                      ask=lambda item: "redact").status, "written")
        self.assertNotIn(HITS[1], target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
