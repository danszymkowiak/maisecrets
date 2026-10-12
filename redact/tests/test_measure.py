"""The measurement on the bench datasets (TASK-34.8): which gold values a configuration hides, which spans it redacts
that touch no gold value, and the vote of several models computed from each model's cached spans.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import unittest

import _home  # noqa: F401  first: a temp plugin home

from maisecrets_redact import measure
from maisecrets_redact.pipeline import Span


def gold(start, end, label, g="pos"):
    return {"start": start, "end": end, "label": label, "gold": g}


class GoldTypeTests(unittest.TestCase):
    def test_dataset_labels_map_to_the_scored_types(self):
        self.assertEqual(measure.gold_type("gretel", "first_name"), "NAME")
        self.assertEqual(measure.gold_type("mendeley", "address"), "ADDRESS")
        self.assertEqual(measure.gold_type("findocs", "AHV"), "NATIONAL_ID")
        self.assertIsNone(measure.gold_type("findocs", "AMOUNT"))


class ScoreTests(unittest.TestCase):
    def test_a_value_counts_as_hidden_when_its_characters_are_mostly_covered(self):
        g = [gold(0, 10, "name"), gold(20, 30, "name")]
        spans = [Span(0, 9, "NAME", "m"), Span(20, 24, "NAME", "m")]   # 90 % and 40 %
        s = measure.Score()
        s.add("gretel", g, spans)
        self.assertEqual(s.found[("gretel", "NAME")], 1)
        self.assertEqual(s.total[("gretel", "NAME")], 2)

    def test_two_spans_together_can_cover_one_value(self):
        s = measure.Score()
        s.add("gretel", [gold(0, 10, "name")], [Span(0, 5, "NAME", "a"), Span(5, 10, "NAME", "b")])
        self.assertEqual(s.found[("gretel", "NAME")], 1)

    def test_a_span_on_negative_gold_or_on_none_is_a_false_positive(self):
        g = [gold(0, 5, "company"), gold(10, 15, "AMOUNT", "neg"), gold(20, 25, "name", "uncertain")]
        spans = [Span(1, 4, "NAME", "m"), Span(11, 14, "NAME", "m"), Span(21, 24, "NAME", "m"),
                 Span(40, 45, "NAME", "m")]
        s = measure.Score()
        s.add("gretel", g, spans)
        self.assertEqual(s.false_pos[("gretel", "NAME")], 2, "the span on a negative gold value and the one on none")

    def test_uncertain_gold_is_not_counted_for_recall(self):
        s = measure.Score()
        s.add("gretel", [gold(0, 5, "name", "uncertain")], [])
        self.assertEqual(s.total[("gretel", "NAME")], 0)


class VoteTests(unittest.TestCase):
    def test_the_vote_redacts_what_every_model_agrees_on_and_sends_the_rest_to_review(self):
        text = "Erika Muster lives at Bahnhofstr. 1"
        rules = []
        per_model = {"a": [Span(0, 12, "NAME", "a"), Span(22, 35, "ADDRESS", "a")], "b": [Span(0, 12, "NAME", "b")]}
        redact, review = measure.vote(text, rules, per_model)
        self.assertEqual([(s.start, s.end) for s in redact], [(0, 12)])
        self.assertEqual([(s.start, s.end) for s in review], [(22, 35)])


if __name__ == "__main__":
    unittest.main()
