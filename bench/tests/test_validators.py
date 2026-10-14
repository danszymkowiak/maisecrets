import unittest

from maisecrets_bench.adapters.plugin import mutations
from maisecrets_bench.domain import mutation
from maisecrets_bench.domain import validators
from maisecrets_bench.domain.bench_error import BenchError


class ChecksumTests(unittest.TestCase):
    def test_aba_routing(self):
        self.assertTrue(validators.aba("011000015"))       # 3*(0+0+0) + 7*(1+0+1) + (1+0+5) = 20
        self.assertFalse(validators.aba("011000016"))
        self.assertTrue(validators.aba("0110-0001-5"), "the dashed Presidio pattern")

    def test_it_fiscal_code(self):
        self.assertTrue(validators.it_fiscal("RSSMRA85T10A562S"))
        self.assertTrue(validators.it_fiscal("rssmra85t10a562s"))
        self.assertFalse(validators.it_fiscal("RSSMRA85T10A562T"))
        self.assertFalse(validators.it_fiscal("RSSMRA85T10A562"))

    def test_se_personnummer(self):
        self.assertTrue(validators.se_pnr("811218-9876"))
        self.assertTrue(validators.se_pnr("19811218-9876"), "the century is not part of the checksum")
        self.assertFalse(validators.se_pnr("811218-9877"))


class PresidioVectorTests(unittest.TestCase):
    """TASK-11.24: the test vectors of Presidio 2.2.364's own tests (presidio-analyzer/tests/test_<name>_recognizer.py
    at tag 2.2.364), for the recognizers whose validate_result the plugin has not ported."""

    def test_es_nif(self):
        for v in ("55555555K", "55555555-K", "1111111-G", "1111111G", "01111111G", "55555555k", "12345678z"):
            self.assertTrue(validators.es_nif(v), v)
        self.assertFalse(validators.es_nif("12345678a"))

    def test_es_nie(self):
        for v in ("Z8078221M", "X9613851N", "Y8063915Z", "Y8063915-Z", "x9613851n", "z8078221m"):
            self.assertTrue(validators.es_nie(v), v)
        for v in ("Y8063915Q", "Y806391Q", "58063915Q", "W8063915Q", "x9613851q"):
            self.assertFalse(validators.es_nie(v), v)

    def test_it_vat_code(self):
        self.assertTrue(validators.it_vat("01333550323"))
        self.assertTrue(validators.it_vat("01333550_323"))
        self.assertFalse(validators.it_vat("00000000000"), "passes the sum, but Presidio rejects it")
        self.assertFalse(validators.it_vat("00000000001"))

    def test_nhs(self):
        for v in ("401-023-2137", "221 395 1837", "0032698674"):
            self.assertTrue(validators.nhs(v), v)
        self.assertFalse(validators.nhs("401-023-2138"))

    def test_us_npi(self):
        for v in ("1234567893", "1245319599", "1003000126", "1234-567-893", "1234 567 893"):
            self.assertTrue(validators.us_npi(v), v)
        self.assertFalse(validators.us_npi("1234567890"), "check digit 3, not 0")
        self.assertFalse(validators.us_npi("1111111112"), "Presidio's invalidate_result: one repeated body digit")

    def test_se_organisationsnummer(self):
        for v in ("212000-0142", "2120000142", "556703-7485", "5567037485"):
            self.assertTrue(validators.se_org(v), v)
        self.assertFalse(validators.se_org("556703-7486"))
        self.assertFalse(validators.se_org("551703-7485"), "third digit below 2")

    def test_uk_vehicle_registration(self):
        for v in ("AB51 ABC", "BD62XYZ", "LN14-HGT", "aa02 aaa", "AB70 DEF"):
            self.assertTrue(validators.uk_vehicle(v), v)
        self.assertFalse(validators.uk_vehicle("AB00 ABC"), "age identifier 00")
        self.assertFalse(validators.uk_vehicle("AB30 ABC"), "age identifier 30: neither March nor September")
        self.assertTrue(validators.uk_vehicle("A123 BCD"), "a prefix-format plate keeps its hit (Presidio: None)")

    def test_each_is_registered(self):
        for name in ("es_nif", "es_nie", "it_vat", "nhs", "us_npi", "se_org", "uk_vehicle"):
            self.assertIn(f"bench:{name}", validators.BENCH)


class MutationFieldTests(unittest.TestCase):
    def test_a_bench_validator_can_be_set_and_is_registered_in_the_detector(self):
        from maisecrets_bench.adapters.plugin.detector import detect
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "email", "validator": "bench:aba"}])
        mutations.validate(m)
        rules = mutations.apply(m, detect.rules())
        self.assertEqual(next(r for r in rules if r.id == "email").validator, "bench:aba")
        self.assertIn("bench:aba", detect.VALIDATORS)

    def test_allow_adds_a_value_filter_to_the_rule_s_own(self):
        from maisecrets_bench.adapters.plugin.detector import detect
        base = next(r for r in detect.rules() if r.id == "generic-api-key")
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "generic-api-key", "allow": ["^[A-Z]+_[a-z]"]}])
        mutations.validate(m)
        rule = next(r for r in mutations.apply(m, detect.rules()) if r.id == "generic-api-key")
        self.assertEqual(len(rule.allow_regexes), len(base.allow_regexes) + 1)
        self.assertEqual(rule.allow_regexes[-1][1], "secret")
        self.assertTrue(rule.allow_regexes[-1][0].search("KEY_value"))

    def test_an_unknown_validator_is_named(self):
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "email", "validator": "bench:nope"}])
        with self.assertRaisesRegex(BenchError, "bench:nope"):
            mutations.validate(m)


if __name__ == "__main__":
    unittest.main()
