"""Valid gold (TASK-21.6): a gold positive of a type with a checksum is checked with the validator the detector uses;
one that fails becomes uncertain, one whose span holds a label around a valid value is trimmed to the value. Made-up
values; the valid ones are published examples or computed here.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import validgold
from maisecrets_bench.schema import Sample, Span

IBAN_OK = "CH93 0076 2011 6238 5295 7"          # the Swiss IBAN example
IBAN_BAD = "DE12 1234 5678 9012 3456 00"         # a generator invention, fails mod 97
CARD_OK = "4111 1111 1111 1111"                  # the common Luhn test number
CARD_BAD = "4111 1111 1111 1112"


def _sample(text: str, value: str, t: str, label: str = "x") -> Sample:
    a = text.index(value)
    return Sample("toy", "s1", "s1", "en", text, [Span(a, a + len(value), label, t, "pos")], "dev")


class CheckTests(unittest.TestCase):
    def one(self, text, value, t):
        (s,), stats = validgold.mark([_sample(text, value, t)])
        return s.spans[0], s.text, stats

    def test_a_valid_value_stays_pos(self):
        sp, text, stats = self.one(f"pay to {IBAN_OK} now", IBAN_OK, "IBAN")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", IBAN_OK))
        self.assertEqual(stats["toy"]["IBAN"], {"pos": 1, "valid": 1, "invalid": 0, "trimmed": 0})

    def test_a_failing_value_becomes_uncertain(self):
        sp, _, stats = self.one(f"pay to {IBAN_BAD} now", IBAN_BAD, "IBAN")
        self.assertEqual(sp.gold, "uncertain")
        self.assertEqual(stats["toy"]["IBAN"]["invalid"], 1)

    def test_a_label_inside_the_span_is_trimmed_off(self):
        sp, text, stats = self.one(f"x IBAN: {IBAN_OK} y", f"IBAN: {IBAN_OK}", "IBAN")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", IBAN_OK))
        self.assertEqual(stats["toy"]["IBAN"]["trimmed"], 1)

    def test_a_card_block_is_trimmed_to_its_number(self):
        block = f"VISA 16 digit\nZed Q\n{CARD_OK.replace(' ', '')} 12/25\nCVC: 351"
        sp, text, _ = self.one(f"card {block} ok", block, "CARD")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", CARD_OK.replace(" ", "")))

    def test_luhn_decides_a_card(self):
        self.assertEqual(self.one(f"c {CARD_OK}.", CARD_OK, "CARD")[0].gold, "pos")
        self.assertEqual(self.one(f"c {CARD_BAD}.", CARD_BAD, "CARD")[0].gold, "uncertain")

    def test_ssn_shape_rules(self):
        for value, gold in (("512-34-5678", "pos"), ("000-12-3456", "uncertain"), ("666-12-3456", "uncertain"),
                            ("912-34-5678", "uncertain"), ("512-00-5678", "uncertain"), ("512-34-0000", "uncertain"),
                            ("512345678", "pos")):
            self.assertEqual(self.one(f"ssn {value} end", value, "US_SSN")[0].gold, gold, value)

    def test_aba_checksum(self):
        self.assertEqual(self.one("aba 011000015 x", "011000015", "ABA_ROUTING_NUMBER")[0].gold, "pos")
        self.assertEqual(self.one("aba 011000016 x", "011000016", "ABA_ROUTING_NUMBER")[0].gold, "uncertain")

    def test_a_type_without_a_checksum_and_neg_spans_are_left_alone(self):
        (s,), stats = validgold.mark([Sample("toy", "s1", "s1", "en", "mail a@b.io and 123",
                                             [Span(5, 11, "e", "EMAIL", "pos"), Span(16, 19, "n", "IBAN", "neg")])])
        self.assertEqual([sp.gold for sp in s.spans], ["pos", "neg"])
        self.assertEqual(stats, {})

    def test_every_checked_type_is_a_type_the_detector_reports(self):
        from maisecrets_bench.detector import known_types
        self.assertEqual(set(validgold.CHECKS), set(validgold._checks()))
        self.assertLessEqual(set(validgold.CHECKS), known_types())


if __name__ == "__main__":
    unittest.main()
