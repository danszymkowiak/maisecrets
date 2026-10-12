"""The generated tax and financial documents (TASK-11.37): Swiss tax and salary forms in German and French, bank
statements, MT940 and CSV exports, US W-2 and 1099 forms and invoices, from a fixed seed. Positives carry valid
checksums; negatives look like them (amounts, dates, references, postal codes, QR references).

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest
from collections import defaultdict

from maisecrets_bench import validators
from maisecrets_bench.adapters import findocs
from maisecrets_bench.detector import detect
from maisecrets_bench.labels import load
from maisecrets_bench.schema import OUT_OF_SCOPE


def _build(n=15, seed=findocs.SEED):
    return list(findocs.samples(load("findocs"), per_template=n, seed=seed))


class ChecksumTests(unittest.TestCase):
    """Published test vectors, never the generator's own output."""

    def test_ahv_ean13(self):
        # 756.1234.5678.97: the example number of the Swiss AHV/AVS documentation
        self.assertEqual(findocs.ean13_check("756123456789"), 7)

    def test_che_uid_mod11(self):
        # python-stdnum ch.uid: CHE-100.155.212 is valid, CHE-100.155.213 is not
        self.assertEqual(findocs.uid_check("10015521"), 2)
        self.assertNotEqual(findocs.uid_check("10015521"), 3)

    def test_qr_reference_mod10_recursive(self):
        # the QR reference of SIX's Swiss QR-bill examples: 21 00000 00003 13947 14300 09017
        self.assertEqual(findocs.mod10_recursive("21000000000313947143000901"), 7)

    def test_aba_and_iban_vectors_hold_in_the_validators_the_bench_scores_with(self):
        self.assertTrue(validators.aba("011000015"))                   # Federal Reserve Bank of Boston
        self.assertTrue(detect._iban_ok("CH93 0076 2011 6238 5295 7"))   # the Swiss IBAN example


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = _build()

    def test_the_same_seed_builds_the_same_text_and_spans(self):
        self.assertEqual([(s.text, s.spans) for s in self.rows], [(s.text, s.spans) for s in _build()])
        self.assertNotEqual([s.text for s in _build(seed=1)], [s.text for s in self.rows])

    def test_every_template_has_pos_and_neg_spans_inside_its_text(self):
        kinds = defaultdict(set)
        for s in self.rows:
            for sp in s.spans:
                self.assertTrue(0 <= sp.start < sp.end <= len(s.text), s.sample_id)
                self.assertEqual(s.text[sp.start:sp.end].strip(), s.text[sp.start:sp.end], "no blank at an edge")
                kinds[s.sample_id.split(":")[0]].add(sp.gold)
        self.assertEqual(set(kinds), set(findocs.TEMPLATES))
        for name, golds in kinds.items():
            self.assertEqual(golds, {"pos", "neg"}, name)

    def test_spans_do_not_overlap(self):
        for s in self.rows:
            ends = sorted((sp.start, sp.end) for sp in s.spans)
            for (a, b), (c, d) in zip(ends, ends[1:]):
                self.assertLessEqual(b, c, s.sample_id)

    def test_the_three_locales_are_there(self):
        self.assertEqual({s.language for s in self.rows}, {"de", "fr", "en"})
        self.assertEqual({t for s in self.rows for t in s.tags if t.startswith("locale:")},
                         {"locale:de_CH", "locale:fr_CH", "locale:en_US"})

    def test_negatives_are_out_of_scope(self):
        for s in self.rows:
            for sp in s.spans:
                if sp.gold == "neg":
                    self.assertEqual(sp.maisecrets_type, OUT_OF_SCOPE, sp.label)

    def test_positives_pass_their_checksums(self):
        checks = {"IBAN": detect._iban_ok, "CARD": lambda v: detect.VALIDATORS["luhn"](v),
                  "ABA": validators.aba,
                  "AHV": lambda v: findocs.ean13_check(v.replace(".", "")[:12]) == int(v[-1]),
                  "CHE_UID": lambda v: findocs.uid_check(v[4:].replace(".", "")[:8]) == int(v[-1]),
                  "QR_REF": lambda v: findocs.mod10_recursive(v.replace(" ", "")[:26]) == int(v[-1])}
        seen = set()
        for s in self.rows:
            for sp in s.spans:
                if sp.label in checks:
                    seen.add(sp.label)
                    self.assertTrue(checks[sp.label](s.text[sp.start:sp.end]), (sp.label, s.sample_id))
        self.assertEqual(seen, set(checks))

    def test_an_ssn_has_a_valid_shape(self):
        for s in self.rows:
            for sp in s.spans:
                if sp.label == "SSN":
                    a, g, n = s.text[sp.start:sp.end].split("-")
                    self.assertTrue(a not in ("000", "666") and a[0] != "9" and g != "00" and n != "0000")

    def test_enough_ahv_numbers_for_the_critical_floor(self):
        # TASK-28: 0.999 needs about 3,000 positives with no miss to show it (one-sided Wilson bound)
        rows = list(findocs.samples(load("findocs")))
        self.assertGreaterEqual(sum(sp.label == "AHV" for s in rows for sp in s.spans), 3000)

    def test_every_generated_name_birth_date_company_and_street_is_a_positive_out_of_scope(self):
        # TASK-36: the names were unlabelled, so redact's models were charged a false positive for each one found
        names: list[str] = []
        real = findocs.FinGen.name

        def recording(g):
            n = real(g)
            names.append(n)
            return n
        from unittest import mock
        with mock.patch.object(findocs.FinGen, "name", recording):
            rows = _build(n=5)
        labelled = {"NAME", "COMPANY", "DOB", "ADDRESS"}
        for s in rows:
            pos = [(sp.start, sp.end) for sp in s.spans if sp.gold == "pos" and sp.label in labelled]
            for sp in s.spans:
                if sp.label in labelled:
                    self.assertEqual((sp.gold, sp.maisecrets_type), ("pos", OUT_OF_SCOPE), sp.label)
            for n in names:
                for form in (n, n.upper()):
                    at = s.text.find(form)
                    while at >= 0:
                        self.assertTrue(any(a <= at and at + len(form) <= b for a, b in pos), (s.sample_id, "name"))
                        at = s.text.find(form, at + 1)
            for word in ("Geburtsdatum ", "Date de naissance "):
                if word in s.text:
                    at = s.text.index(word) + len(word)
                    self.assertIn("DOB", [sp.label for sp in s.spans if sp.start == at], s.sample_id)
            for street in ("Bahnhofstrasse 12", "Rue du Rhône 8", "400 Market St", "Rue de Lausanne 14"):
                if street in s.text:
                    at = s.text.index(street)
                    self.assertTrue(any(sp.label == "ADDRESS" and sp.start <= at < sp.end for sp in s.spans), street)
            for company in (" Treuhand AG", " SA, IDE", " Logistics Inc"):
                if company in s.text:
                    at = s.text.index(company)
                    self.assertTrue(any(sp.label == "COMPANY" and sp.start < at < sp.end for sp in s.spans), company)

    def test_the_version_names_seed_and_size(self):
        self.assertIn(f"seed{findocs.SEED}-n{findocs.PER_TEMPLATE}-", findocs.version())


if __name__ == "__main__":
    unittest.main()
