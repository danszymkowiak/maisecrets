"""IBAN forms the vendored Presidio rule missed (TASK-22): the counterparty IBAN of an MT940 :86: field after its ?31
subfield code (?30 BIC, ?32/?33 name around it), and an IBAN written in lowercase. Both stay gated by mod 97; a
lowercase one must also have its country's length, since a lowercase hex digest can pass mod 97 by chance.

Run: python3 -m unittest tests.test_iban_forms -v
The IBANs are the registry's public examples.
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

DE = "DE89370400440532013000"
CH = "CH9300762011623852957"
GB = "GB82WEST12345698765432"


def broken(iban: str) -> str:
    """The same IBAN with one digit of the account changed: mod 97 fails."""
    i = len(iban) - 3
    return iban[:i] + str((int(iban[i]) + 1) % 10) + iban[i + 1:]


def ibans(text: str) -> list[str]:
    return [m.value for m in detect.scan(text) if m.type == "IBAN"]


class Mt940Tests(unittest.TestCase):
    def test_the_counterparty_iban_after_its_subfield_code_is_found(self):
        for iban in (DE, CH, GB):
            for text in (f":86:166?00SEPA-UEBERWEISUNG?20Miete?30COBADEFFXXX?31{iban}?32MAX MUSTERMANN",
                         f"?31{iban}", f"?30INGDDEFFXXX?31{iban}?32", f"?31{iban}\n?32Firma"):
                with self.subTest(text=text):
                    self.assertEqual(ibans(text), [iban])

    def test_a_slash_before_the_iban_still_counts(self):
        self.assertEqual(ibans(f":59:/{DE}\nMax Mustermann"), [DE])
        self.assertEqual(ibans(f"/IBAN/{DE}/"), [DE])

    def test_a_failing_checksum_after_a_subfield_code_is_no_hit(self):
        for iban in (DE, CH, GB):
            with self.subTest(iban=iban):
                self.assertEqual(ibans(f"?30COBADEFFXXX?31{broken(iban)}?32NAME"), [])

    def test_digits_that_are_not_a_subfield_code_still_block(self):
        # the vendored left boundary stays for any other digit or letter run
        self.assertEqual(ibans(f"x31{DE}"), [])
        self.assertEqual(ibans(f"731{DE}"), [])


class LowercaseTests(unittest.TestCase):
    def test_a_lowercase_iban_is_found_plain_and_spaced(self):
        spaced = " ".join(DE[i:i + 4] for i in range(0, len(DE), 4))
        for text, want in ((f"iban: {DE.lower()}", DE.lower()), (f"IBAN {spaced.lower()}", spaced.lower()),
                           (f"?31{CH.lower()}?32", CH.lower()), (f"pay to {GB.lower()} today", GB.lower())):
            with self.subTest(text=text):
                self.assertEqual(ibans(text), [want])

    def test_a_lowercase_mod97_failure_is_no_hit(self):
        for iban in (DE, CH, GB):
            with self.subTest(iban=iban):
                self.assertEqual(ibans(f"iban {broken(iban).lower()}"), [])

    def test_a_lowercase_value_needs_its_country_length(self):
        # a 32-character lowercase hex digest that passes mod 97: DE IBANs have 22 characters, so it is no IBAN
        digest = next(h for h in (f"de{n:02d}" + format(k, "028x") for n in range(10, 100) for k in range(1, 4000))
                      if detect._iban_ok(h.upper()))
        self.assertTrue(detect._iban_ok(digest.upper()), "the premise: it passes mod 97")
        self.assertFalse(detect._iban_ok(digest), "in lower case it needs its country's length too")
        self.assertEqual(ibans(f"commit {digest} merged"), [])
        self.assertEqual(ibans(f"commit {digest.upper()} merged"), [digest.upper()],
                         "upper case keeps the vendored behaviour: mod 97 alone")

    def test_a_lowercase_value_with_an_unknown_country_is_no_hit(self):
        # QQ is no IBAN country; the check digits are made to pass mod 97
        body = "12345678901234567890"
        for cd in range(2, 99):
            cand = f"qq{cd:02d}{body}"
            if detect._iban_ok(cand.upper()):
                break
        self.assertTrue(detect._iban_ok(cand.upper()))
        self.assertEqual(ibans(f"ref {cand}"), [])


class HyphenTests(unittest.TestCase):
    """TASK-29: the vendored pattern takes hyphens between the groups, the validator stripped only spaces."""

    def test_a_hyphenated_iban_is_found(self):
        for iban in (DE, CH, GB):
            dashed = "-".join(iban[i:i + 4] for i in range(0, len(iban), 4))
            with self.subTest(iban=dashed):
                self.assertTrue(detect._iban_ok(dashed))
                self.assertEqual(ibans(f"IBAN {dashed}"), [dashed])
                self.assertEqual(ibans(f"IBAN {dashed.lower()}"), [dashed.lower()])

    def test_a_hyphenated_mod97_failure_is_no_hit(self):
        for iban in (DE, CH, GB):
            dashed = "-".join(broken(iban)[i:i + 4] for i in range(0, len(iban), 4))
            with self.subTest(iban=dashed):
                self.assertFalse(detect._iban_ok(dashed))
                self.assertEqual(ibans(f"IBAN {dashed}"), [])


if __name__ == "__main__":
    unittest.main()
