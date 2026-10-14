"""Valid gold (TASK-21.6): a gold positive of a type with a checksum is checked with the validator the detector uses;
one that fails becomes uncertain, one whose span holds a label around a valid value is trimmed to the value. Made-up
values; the valid ones are published examples or computed here.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench.adapters import compose
from maisecrets_bench.adapters.plugin import gold as plugin_gold
from maisecrets_bench.domain import validgold
from maisecrets_bench.adapters.plugin.detector import detect
from maisecrets_bench.domain.samples import Sample, Span

IBAN_OK = "CH93 0076 2011 6238 5295 7"          # the Swiss IBAN example
IBAN_BAD = "DE12 1234 5678 9012 3456 00"         # a generator invention, fails mod 97
CARD_OK = "4111 1111 1111 1111"                  # the common Luhn test number
CARD_BAD = "4111 1111 1111 1112"


def _sample(text: str, value: str, t: str, label: str = "x") -> Sample:
    a = text.index(value)
    return Sample("toy", "s1", "s1", "en", text, [Span(a, a + len(value), label, t, "pos")], "dev")


class CheckTests(unittest.TestCase):
    def one(self, text, value, t):
        (s,), stats = compose.mark_gold([_sample(text, value, t)])
        return s.spans[0], s.text, stats

    def test_a_valid_value_stays_pos(self):
        sp, text, stats = self.one(f"pay to {IBAN_OK} now", IBAN_OK, "IBAN")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", IBAN_OK))
        self.assertEqual(stats["toy"]["IBAN"], {"pos": 1, "valid": 1, "invalid": 0, "trimmed": 0, "negative": 0,
                                                "retyped": 0})

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

    def test_a_type_without_a_check_and_neg_spans_are_left_alone(self):
        (s,), stats = compose.mark_gold([Sample("toy", "s1", "s1", "en", "key abcdef and 123",
                                             [Span(4, 10, "k", "SECRET", "pos"), Span(15, 18, "n", "IBAN", "neg")])])
        self.assertEqual([sp.gold for sp in s.spans], ["pos", "neg"])
        self.assertEqual(stats, {})

    def test_every_checked_type_is_a_type_the_detector_reports(self):
        from maisecrets_bench.adapters.plugin.detector import known_types
        self.assertEqual(set(validgold.CHECKS), set(plugin_gold.checks()))
        self.assertLessEqual(set(validgold.CHECKS), known_types())


def _iban(country: str, bban: str) -> str:
    """A valid IBAN for a made-up account: the check digits computed here."""
    num = int("".join(str(ord(c) - 55) if c.isalpha() else c for c in bban + country + "00"))
    return f"{country}{98 - num % 97:02d}{bban}"


def _spaced(v: str) -> str:
    return " ".join(v[i:i + 4] for i in range(0, len(v), 4))


class ShrinkTests(unittest.TestCase):
    """TASK-31: a cut may only drop text the pattern took after the value (an expiry after a card number), never a
    group of the value itself: a fake IBAN or card cut at a group boundary passes its checksum by chance (1 in 97,
    1 in 10) and the gold became a fragment no detector reports."""

    def one(self, text, value, t):
        (s,), _ = compose.mark_gold([_sample(text, value, t)])
        return s.spans[0], s.text

    def test_a_fake_iban_is_not_cut_to_a_prefix_that_passes(self):
        n = 0
        for k in range(2000):
            head = _iban("FR", f"{k:016d}")                  # a valid 20-character IBAN
            whole = _spaced(head + "233167")                  # the same with two more groups: almost always fake
            if detect._iban_ok(whole):
                continue
            n += 1
            with self.subTest(whole=whole):
                sp, _ = self.one(f"account {whole} x", whole, "IBAN")
                self.assertEqual(sp.gold, "uncertain")
            if n == 20:
                break

    def test_a_fake_card_is_not_cut_to_a_prefix_that_passes(self):
        sp, _ = self.one(f"card {CARD_OK} 1234 x", f"{CARD_OK} 1234", "CARD")
        self.assertEqual(sp.gold, "uncertain")

    def test_an_expiry_after_the_number_is_still_cut_off(self):
        for value in (f"{CARD_OK} 12/25", f"{CARD_OK.replace(' ', '')} 12/25"):
            with self.subTest(value=value):
                sp, text = self.one(f"card {value} x", value, "CARD")
                self.assertEqual((sp.gold, text[sp.start:sp.end].replace(" ", "")), ("pos", CARD_OK.replace(" ", "")))

    def test_a_cut_inside_a_group_is_refused(self):
        sp, _ = self.one("card 41111111111111112 x", "41111111111111112", "CARD")
        self.assertEqual(sp.gold, "uncertain")


class ValidityTests(unittest.TestCase):
    """TASK-30: types without a checksum get the validity rules the gold audit chose (maisecrets_bench/audit.py). A
    span that is no value of its type at all becomes negative; an IBAN labelled as a bank number becomes IBAN."""

    def one(self, text, value, t):
        (s,), stats = compose.mark_gold([_sample(text, value, t)])
        return s.spans[0], s.text, stats

    def test_a_plausible_phone_stays_and_a_placeholder_number_becomes_uncertain(self):
        self.assertEqual(self.one("call +41 44 668 18 00 now", "+41 44 668 18 00", "PHONE")[0].gold, "pos")
        self.assertEqual(self.one("call 030-438-8690 now", "030-438-8690", "PHONE")[0].gold, "pos")
        for v in ("(123) 456-7890", "555-555-5555", "(494) 360-7563", "12345"):
            with self.subTest(v=v):
                self.assertEqual(self.one(f"call {v} now", v, "PHONE")[0].gold, "uncertain")

    def test_brackets_around_a_value_are_trimmed(self):
        sp, text, stats = self.one("tel [+41 44 668 18 00] x", "[+41 44 668 18 00]", "PHONE")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", "+41 44 668 18 00"))
        sp, text, _ = self.one("mail [max@firma.ch] x", "[max@firma.ch]", "EMAIL")
        self.assertEqual((sp.gold, text[sp.start:sp.end]), ("pos", "max@firma.ch"))

    def test_a_span_with_nothing_of_its_type_becomes_negative(self):
        for text, value, t in (("Tel: [Phone Number] x", "[Phone Number]", "PHONE"),
                               ("die adresse e-mail professionnelle", "adresse e-mail professionnelle", "EMAIL"),
                               ("ip [IP address] x", "[IP address]", "IP")):
            with self.subTest(value=value):
                sp, _, stats = self.one(text, value, t)
                self.assertEqual(sp.gold, "neg")
                self.assertEqual(stats["toy"][t]["negative"], 1)

    def test_reserved_mail_and_non_public_addresses_become_uncertain(self):
        self.assertEqual(self.one("mail max@example.com x", "max@example.com", "EMAIL")[0].gold, "uncertain")
        self.assertEqual(self.one("ip 192.168.0.1 x", "192.168.0.1", "IP")[0].gold, "uncertain")
        self.assertEqual(self.one("ip 93.184.216.34 x", "93.184.216.34", "IP")[0].gold, "pos")

    def test_an_iban_labelled_as_a_bank_number_becomes_iban(self):
        sp, text, stats = self.one(f"account {IBAN_OK} x", IBAN_OK, "US_BANK_NUMBER")
        self.assertEqual((sp.gold, sp.maisecrets_type), ("pos", "IBAN"))
        self.assertEqual(stats["toy"]["US_BANK_NUMBER"]["retyped"], 1)
        self.assertEqual(self.one(f"account {IBAN_BAD} x", IBAN_BAD, "US_BANK_NUMBER")[0].gold, "uncertain")
        self.assertEqual(self.one("account 000123456789 x", "000123456789", "US_BANK_NUMBER")[0].gold, "pos")
        self.assertEqual(self.one("account C82376415 x", "C82376415", "US_BANK_NUMBER")[0].gold, "uncertain")


if __name__ == "__main__":
    unittest.main()
