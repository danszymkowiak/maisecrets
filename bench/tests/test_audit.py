"""The gold audit (TASK-30): candidate validity rules per type, each a function of the gold value that names why it is
no valid value, or None. The audit counts them per dataset and type before any rule is applied to the gold."""
from __future__ import annotations

import unittest

from maisecrets_bench import audit, schema


def fails(t: str, value: str) -> set[str]:
    return {name for name, why in audit.reasons(t, value)}


class PhoneTests(unittest.TestCase):
    def test_plausible_numbers_pass(self):
        for v in ("+41 44 668 18 00", "(212) 555-0147", "212-555-0147", "+1 212 555 0147", "030 1234567",
                  "+49 (0)30 123456", "0044 20 7946 0958", "212.555.0147 ext. 12"):
            with self.subTest(v=v):
                self.assertEqual(fails("PHONE", v), set())

    def test_digit_count_outside_e164(self):
        self.assertIn("phone-digits", fails("PHONE", "12345"))
        self.assertIn("phone-digits", fails("PHONE", "+49 1234 5678 9012 3456"))

    def test_letters_other_than_an_extension(self):
        self.assertIn("phone-letters", fails("PHONE", "555-CALL-NOW"))
        self.assertNotIn("phone-letters", fails("PHONE", "212-555-0147 x12"))

    def test_a_north_american_number_outside_the_plan(self):
        for v in ("(212) 155-0147", "+1 112 555 0147", "1-212-055-0147", "+1 012 555 0147"):
            with self.subTest(v=v):
                self.assertIn("phone-nanp", fails("PHONE", v))
        # a 10-digit number without a +1 or a US layout is not judged by the US plan
        self.assertNotIn("phone-nanp", fails("PHONE", "0301234567"))
        # a leading 0 is a trunk prefix outside North America (UK, Germany, Korea): not judged by the US plan
        for v in ("030-438-8690", "(022) 739-3821", "031 567 4983", "072-699 5490"):
            with self.subTest(v=v):
                self.assertEqual(fails("PHONE", v), set())
        # a US layout with a 1 first is a placeholder, not a foreign number
        for v in ("(123) 456-7890", "123-456-7890", "(800) 123-4567"):
            with self.subTest(v=v):
                self.assertIn("phone-nanp", fails("PHONE", v))

    def test_a_reserved_area_code_is_its_own_reason(self):
        self.assertEqual(fails("PHONE", "(494) 360-7563"), {"phone-nanp-reserved"})

    def test_one_repeated_digit(self):
        self.assertIn("phone-repeated", fails("PHONE", "000-000-0000"))


class EmailTests(unittest.TestCase):
    def test_addresses_pass(self):
        for v in ("max.muster@firma.ch", "a+b@sub.example.de", "o'neil@mail.co.uk"):
            with self.subTest(v=v):
                self.assertEqual(fails("EMAIL", v), set())

    def test_broken_syntax(self):
        for v in ("max.muster@", "@firma.ch", "max muster@firma.ch", "max@firma", "max@@firma.ch", "max@firma.c0m"):
            with self.subTest(v=v):
                self.assertIn("email-syntax", fails("EMAIL", v))

    def test_a_reserved_domain_is_its_own_reason(self):
        self.assertEqual(fails("EMAIL", "max@example.com"), {"email-reserved"})
        self.assertEqual(fails("EMAIL", "max@shop.test"), {"email-reserved"})


class IpTests(unittest.TestCase):
    def test_public_addresses_pass(self):
        for v in ("93.184.216.34", "2a00:1450:4001::200e"):
            self.assertEqual(fails("IP", v), set())

    def test_unparseable(self):
        for v in ("256.1.1.1", "1.2.3", "10.0.0.1/24x", "zz::zz"):
            with self.subTest(v=v):
                self.assertIn("ip-parse", fails("IP", v))

    def test_a_non_public_address_is_its_own_reason(self):
        for v in ("10.1.2.3", "192.168.0.1", "127.0.0.1", "fe80::1"):
            with self.subTest(v=v):
                self.assertEqual(fails("IP", v), {"ip-non-public"})


class BankNumberTests(unittest.TestCase):
    def test_account_numbers_pass(self):
        for v in ("000123456789", "12345678", "1234-5678-9012"):
            self.assertEqual(fails("US_BANK_NUMBER", v), set())

    def test_digit_count_and_letters(self):
        self.assertIn("bank-digits", fails("US_BANK_NUMBER", "123"))
        self.assertIn("bank-digits", fails("US_BANK_NUMBER", "1" * 18))
        self.assertIn("bank-letters", fails("US_BANK_NUMBER", "12AB5678"))


class AuditTests(unittest.TestCase):
    def test_counts_per_dataset_type_and_reason_with_masked_examples(self):
        text = "call (112) 555-0147 or (212) 555-0147, mail max@example.com"
        spans = [schema.Span(5, 19, "PHONE", "PHONE", "pos"), schema.Span(23, 37, "PHONE", "PHONE", "pos"),
                 schema.Span(44, 59, "EMAIL", "EMAIL", "pos"), schema.Span(0, 4, "X", schema.OUT_OF_SCOPE, "pos")]
        s = schema.Sample("d", "s1", "s1", "en", text, spans)
        out = audit.audit([s])
        self.assertEqual(out["d"]["PHONE"]["total"], 2)
        self.assertEqual(out["d"]["PHONE"]["reasons"]["phone-nanp"]["count"], 1)
        self.assertEqual(out["d"]["EMAIL"]["reasons"]["email-reserved"]["count"], 1)
        self.assertNotIn(schema.OUT_OF_SCOPE, out["d"])
        examples = out["d"]["PHONE"]["reasons"]["phone-nanp"]["examples"]
        self.assertEqual(examples, ["(9+) 9+-9+"])
        self.assertNotIn("012", str(out))

    def test_uncertain_gold_is_audited_apart(self):
        s = schema.Sample("d", "s1", "s1", "en", "x 12345", [schema.Span(2, 7, "PHONE", "PHONE", "uncertain")])
        out = audit.audit([s])
        self.assertEqual(out["d"]["PHONE"]["total"], 0)
        self.assertEqual(out["d"]["PHONE"]["uncertain"], 1)


if __name__ == "__main__":
    unittest.main()
