import unittest

from maisecrets_bench import mutation, validators
from maisecrets_bench.paths import BenchError


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


class MutationFieldTests(unittest.TestCase):
    def test_a_bench_validator_can_be_set_and_is_registered_in_the_detector(self):
        from maisecrets_bench.detector import detect
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "email", "validator": "bench:aba"}])
        mutation.validate(m)
        rules = mutation.apply(m, detect.rules())
        self.assertEqual(next(r for r in rules if r.id == "email").validator, "bench:aba")
        self.assertIn("bench:aba", detect.VALIDATORS)

    def test_allow_adds_a_value_filter_to_the_rule_s_own(self):
        from maisecrets_bench.detector import detect
        base = next(r for r in detect.rules() if r.id == "generic-api-key")
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "generic-api-key", "allow": ["^[A-Z]+_[a-z]"]}])
        mutation.validate(m)
        rule = next(r for r in mutation.apply(m, detect.rules()) if r.id == "generic-api-key")
        self.assertEqual(len(rule.allow_regexes), len(base.allow_regexes) + 1)
        self.assertEqual(rule.allow_regexes[-1][1], "secret")
        self.assertTrue(rule.allow_regexes[-1][0].search("KEY_value"))

    def test_an_unknown_validator_is_named(self):
        m = mutation.Mutation("x", "", [{"op": "set", "rule": "email", "validator": "bench:nope"}])
        with self.assertRaisesRegex(BenchError, "bench:nope"):
            mutation.validate(m)


if __name__ == "__main__":
    unittest.main()
