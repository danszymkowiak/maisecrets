"""The Swiss region (TASK-20): the AHV/AVS number and the company UID with their check digits, context words in German,
French and Italian, and the region `ch` selecting them with the de, fr and it label languages.

Run: python3 -m unittest tests.test_swiss_region -v
The published examples are the ones the issuers print (AHV: the Zentrale Ausgleichsstelle; UID: eCH-0097); every
other number is generated here from its check digit.
"""
from __future__ import annotations

import os
import random
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect, regions  # noqa: E402

AHV_EXAMPLE = "756.9217.0769.85"     # the ZAS example
UID_EXAMPLE = "CHE-123.456.788"      # the eCH-0097 example
_R = random.Random(20)


def ahv(r: random.Random = _R) -> str:
    """A valid AHV number, 13 digits: 756, 9 digits, the EAN-13 check digit."""
    body = "756" + "".join(r.choice("0123456789") for _ in range(9))
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body))
    return body + str((10 - total % 10) % 10)


def dotted(n: str) -> str:
    return f"{n[:3]}.{n[3:7]}.{n[7:11]}.{n[11:]}"


def uid(r: random.Random = _R) -> str:
    """A valid UID: 8 digits and the mod-11 check digit (a check of 10 is never issued)."""
    while True:
        body = "".join(r.choice("0123456789") for _ in range(8))
        check = 11 - sum(int(d) * w for d, w in zip(body, (5, 4, 3, 2, 7, 6, 5, 4))) % 11
        if check != 10:
            n = body + str(check % 11)
            return f"CHE-{n[:3]}.{n[3:6]}.{n[6:]}"


def bad_check(n: str) -> str:
    last = n[-1]
    return n[:-1] + str((int(last) + 1) % 10)


class ValidatorTests(unittest.TestCase):
    def test_the_published_examples_pass(self):
        self.assertTrue(detect.VALIDATORS["ch_ahv"](AHV_EXAMPLE))
        self.assertTrue(detect.VALIDATORS["ch_ahv"](AHV_EXAMPLE.replace(".", "")))
        self.assertTrue(detect.VALIDATORS["ch_uid"](UID_EXAMPLE))
        self.assertTrue(detect.VALIDATORS["ch_uid"](UID_EXAMPLE + " MWST"))

    def test_a_wrong_check_digit_fails(self):
        for _ in range(50):
            a, u = ahv(), uid()
            with self.subTest(ahv=a, uid=u):
                self.assertTrue(detect.VALIDATORS["ch_ahv"](a))
                self.assertFalse(detect.VALIDATORS["ch_ahv"](bad_check(a)))
                self.assertTrue(detect.VALIDATORS["ch_uid"](u))
                self.assertFalse(detect.VALIDATORS["ch_uid"](bad_check(u)))

    def test_an_ahv_number_must_start_with_756(self):
        a = ahv()
        other = "757" + a[3:12]
        total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(other))
        self.assertFalse(detect.VALIDATORS["ch_ahv"](other + str((10 - total % 10) % 10)))


class SwissRegionTests(unittest.TestCase):
    SWISS = detect.build(detect.Settings(regions=("generic", "ch"), languages=("en", "de", "fr", "it")))

    def kinds(self, text: str, ruleset=SWISS) -> list:
        return [(m.kind, m.value) for m in detect.scan(text, ruleset=ruleset) if m.kind.startswith("ch-")]

    def test_the_dotted_ahv_number_is_found_in_every_language(self):
        a = dotted(ahv())
        for text in (f"AHV-Nr. {a}", f"numéro AVS : {a}", f"numero AVS: {a}", f"Versichertennummer {a}", a):
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text), [("ch-ahv", a)])

    def test_the_bare_ahv_number_needs_its_context_word(self):
        a = ahv()
        self.assertEqual(self.kinds(f"AHV {a}"), [("ch-ahv", a)])
        self.assertEqual(self.kinds(f"no. AVS {a}"), [("ch-ahv", a)])
        self.assertEqual(self.kinds(f"order {a} shipped"), [])

    def test_a_number_that_fails_its_check_digit_is_no_hit(self):
        a = ahv()
        self.assertEqual(self.kinds(f"AHV {dotted(bad_check(a))}"), [])
        self.assertEqual(self.kinds(f"AHV {bad_check(a)}"), [])
        u = uid()
        self.assertEqual(self.kinds(f"UID {bad_check(u)}"), [])

    def test_the_uid_is_found_with_and_without_its_vat_suffix(self):
        u = uid()
        for text, want in ((f"UID: {u}", u), (f"{u} MWST", f"{u} MWST"), (f"{u} TVA", f"{u} TVA"),
                           (f"N° IDE {u} IVA", f"{u} IVA"), (f"Firma {u}", u)):
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text), [("ch-uid", want)])

    def test_a_swiss_iban_and_phone_number_are_already_covered(self):
        iban = "CH93 0076 2011 6238 5295 7"                # the IBAN registry's Swiss example
        self.assertIn(("IBAN", iban), [(m.type, m.value) for m in detect.scan(f"IBAN {iban}", ruleset=self.SWISS)])
        self.assertIn("PHONE", [m.type for m in detect.scan("Tel. +41 44 668 18 00", ruleset=self.SWISS)])

    def test_without_the_region_no_swiss_rule_runs(self):
        german = detect.build(detect.Settings(regions=("generic", "de"), languages=("en", "de")))
        self.assertEqual(self.kinds(f"AHV-Nr. {dotted(ahv())}", german), [])


class ResolveTests(unittest.TestCase):
    def test_region_ch_brings_german_french_and_italian_labels(self):
        with mock.patch.dict(os.environ, {"MAISECRETS_LOCALE": "C"}):
            active = regions.resolve({"regions": ["ch"]})
        self.assertEqual(active.regions, ("generic", "ch"))
        self.assertEqual(active.languages, ("en", "de", "fr", "it"))

    def test_a_swiss_locale_resolves_auto_to_ch(self):
        for loc, lang in (("de_CH.UTF-8", "de"), ("fr-CH", "fr"), ("it_CH", "it")):
            with self.subTest(loc=loc), mock.patch.dict(os.environ, {"MAISECRETS_LOCALE": loc}):
                active = regions.resolve({})
                self.assertEqual(active.regions, ("generic", "ch"))
                self.assertEqual(active.languages[:2], ("en", lang))
                self.assertEqual(set(active.languages), {"en", "de", "fr", "it"})


if __name__ == "__main__":
    unittest.main()
