"""Rule mutations (docs/BENCHMARK.md, Judging a change): a TOML file that disables, changes or adds rules, applied to
the detector's rule list inside the bench, never to the plugin; and the judgement against the baseline.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import detector, mutation
from maisecrets_bench.paths import BenchError
from maisecrets_bench.score import Counts

D = detector.detect
MAIL = "zq.tester@example-mail.org"


def _load(text: str) -> mutation.Mutation:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.toml"
        p.write_text(text, encoding="utf-8")
        return mutation.load(p)


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.base = list(D.rules())

    def scan_with(self, m: mutation.Mutation, text: str) -> list:
        rs = mutation.ruleset(m, D.default_ruleset())
        return [(x.kind, x.type) for x in D.scan(text, ruleset=rs)]

    def test_disable_removes_the_rule(self):
        m = _load('name = "no email"\n[[change]]\nop = "disable"\nrule = "email"\n')
        self.assertIn(("email", "EMAIL"), self.scan_with(mutation.Mutation("none", "", []), f"to {MAIL}"))
        self.assertNotIn(("email", "EMAIL"), self.scan_with(m, f"to {MAIL}"))

    def test_add_puts_a_new_rule_in(self):
        m = _load('name = "zz"\n[[change]]\nop = "add"\nid = "zz-token"\ntype = "SECRET"\nregex = "ZZTOK[0-9]{6}"\n')
        self.assertIn(("zz-token", "SECRET"), self.scan_with(m, "value ZZTOK123456 here"))

    def test_set_changes_a_field_of_a_rule(self):
        m = _load('name = "narrow"\n[[change]]\nop = "set"\nrule = "email"\nregex = "nomatch@nowhere\\\\.invalid"\n')
        self.assertNotIn(("email", "EMAIL"), self.scan_with(m, f"to {MAIL}"))

    def test_the_plugin_rules_stay_untouched(self):
        before = [r.id for r in self.base]
        mutation.apply(_load('name = "x"\n[[change]]\nop = "disable"\nrule = "email"\n'), self.base)
        self.assertEqual([r.id for r in self.base], before)

    def test_an_unknown_rule_is_named(self):
        with self.assertRaisesRegex(BenchError, "'no-such-rule'"):
            mutation.apply(_load('name = "x"\n[[change]]\nop = "disable"\nrule = "no-such-rule"\n'), self.base)

    def test_an_unknown_field_is_named(self):
        with self.assertRaisesRegex(BenchError, "'colour'"):
            mutation.apply(_load('name = "x"\n[[change]]\nop = "set"\nrule = "email"\ncolour = "red"\n'), self.base)

    def test_a_rule_of_another_region_is_skipped_in_a_group_without_it(self):
        # us-bank exists in the English group only; the German group must run the mutation too (round 1, 2026-10-11)
        m = _load('name = "x"\n[[change]]\nop = "disable"\nrule = "us-bank"\n')
        without = [r for r in self.base if r.id != "us-bank"]
        self.assertEqual([r.id for r in mutation.apply(m, without, strict=False)], [r.id for r in without])

    def test_validation_knows_the_rules_of_every_region(self):
        mutation.validate(_load('name = "x"\n[[change]]\nop = "disable"\nrule = "it-fiscal-code"\n'))
        with self.assertRaisesRegex(BenchError, "'no-such-rule'"):
            mutation.validate(_load('name = "x"\n[[change]]\nop = "disable"\nrule = "no-such-rule"\n'))

    def test_normalise_turns_the_normaliser_stages_on(self):
        # TASK-11.25: a token split by an ANSI reset is found once the stage is on
        text = "use ghp_" + "A1b2C3d4E5f6G7h8I9" + "\x1b[0m" + "j0K1l2M3n4O5p6Q7r8"
        self.assertEqual(self.scan_with(mutation.Mutation("none", "", []), text), [])
        m = _load('name = "ansi"\n[[change]]\nop = "normalise"\nstages = ["ansi"]\n')
        self.assertEqual([t for _, t in self.scan_with(m, text)], ["SECRET"])
        self.assertFalse(m.disable_only)
        mutation.validate(m)

    def test_an_unknown_normaliser_stage_is_named(self):
        with self.assertRaisesRegex(BenchError, "'rot13'"):
            mutation.validate(_load('name = "x"\n[[change]]\nop = "normalise"\nstages = ["rot13"]\n'))

    def test_unfix_switches_one_named_check_off(self):
        # url-query-secret drops a template value ({...}) by its fix "template-braces" (TASK-26)
        text = "GET https://api.example.org/x?token={SLACK_AUTO_TOKEN}"
        self.assertEqual([(x.kind, x.type) for x in D.scan(text)], [])
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "unfix"\nfix = "template-braces"\n'
                  'rule = "url-query-secret"\n')
        self.assertEqual(self.scan_with(m, text), [("url-query-secret", "SECRET")])
        self.assertIn("template-braces", next(r for r in D.rules() if r.id == "url-query-secret").fixes,
                      "the plugin's rule keeps its fix")

    def test_unfix_without_a_rule_takes_the_fix_off_every_rule(self):
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "unfix"\nfix = "code-value"\n')
        rules = mutation.apply(m, self.base)
        self.assertFalse([r.id for r in rules if "code-value" in r.fixes])
        self.assertTrue([r.id for r in self.base if "code-value" in r.fixes])

    def test_an_unknown_fix_is_named(self):
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "unfix"\nfix = "rocket"\n')
        with self.assertRaisesRegex(BenchError, "rocket"):
            mutation.validate(m)

    def test_vendored_swaps_the_vendored_secret_set(self):
        # TASK-19.3: the switch to Betterleaks judged like any change
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "vendored"\nset = "betterleaks"\n'
                  '[[change]]\nop = "disable"\nrule = "jwt"\n')
        mutation.validate(m)
        ids = {r.id for r in mutation.ruleset(m, D.default_ruleset()).rules}
        self.assertIn("aikido-ci-token", ids)
        self.assertNotIn("jwt", ids, "the later changes apply to the swapped set")
        self.assertIn("email", ids, "the other rules stay")
        self.assertIn("aikido-ci-token", {r.id for r in D.rules()}, "Betterleaks is the default since TASK-19.4")

    def test_carry_takes_a_rule_from_the_other_vendored_set(self):
        # TASK-19.8: Betterleaks with gitleaks' generic-api-key in place of its own
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "vendored"\nset = "betterleaks"\n'
                  '[[change]]\nop = "carry"\nrule = "generic-api-key"\nfrom = "carried"\n')
        mutation.validate(m)
        rules = mutation.ruleset(m, D.default_ruleset()).rules
        gak = [r for r in rules if r.id == "generic-api-key"]
        self.assertEqual(len(gak), 1)
        gitleaks = next(r for r in D._load_carried() if r.id == "generic-api-key")
        self.assertEqual((gak[0].regex.pattern, gak[0].entropy, gak[0].filter), (gitleaks.regex.pattern, 3.5, None))
        self.assertIn("aikido-ci-token", {r.id for r in rules})

    def test_carry_of_an_unknown_rule_is_named(self):
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "carry"\nrule = "no-such"\nfrom = "carried"\n')
        with self.assertRaisesRegex(BenchError, "no-such"):
            mutation.validate(m)

    def test_an_unknown_vendored_set_is_named(self):
        m = _load('name = "n"\nwhy = "w"\n[[change]]\nop = "vendored"\nset = "trufflehog"\n')
        with self.assertRaisesRegex(BenchError, "trufflehog"):
            mutation.validate(m)

    def test_a_disable_only_mutation_says_so(self):
        self.assertTrue(_load('name = "x"\n[[change]]\nop = "disable"\nrule = "email"\n').disable_only)
        self.assertFalse(_load('name = "x"\n[[change]]\nop = "set"\nrule = "email"\nentropy = 3.0\n').disable_only)


class JudgeTests(unittest.TestCase):
    BASE = {"a": Counts(tp=80, fp=20, found=60, fn=40, samples=100, clean=90),
            "b": Counts(tp=50, fp=50, found=50, fn=50, samples=100, clean=60),
            "g": Counts(fp=4, samples=1000, clean=996)}

    def test_better_everywhere_is_accepted_and_ranked_by_the_mean_of_the_scored(self):
        mut = dict(self.BASE, b=Counts(tp=50, fp=10, found=50, fn=50, samples=100, clean=90))
        j = mutation.judge(self.BASE, mut, {"g": "guard"})
        self.assertTrue(j["accepted"])
        self.assertGreater(j["overall_delta"], 0)
        self.assertEqual(set(j["datasets"]), {"a", "b", "g"})

    def test_a_loss_of_recall_anywhere_rejects(self):
        mut = dict(self.BASE, a=Counts(tp=80, fp=0, found=59, fn=41, samples=100, clean=100))
        j = mutation.judge(self.BASE, mut, {})
        self.assertFalse(j["accepted"])
        self.assertIn("a: recall", " ".join(j["reasons"]))

    def test_a_guard_dataset_rejects_when_it_gets_worse_but_has_no_weight(self):
        worse_guard = dict(self.BASE, g=Counts(fp=9, samples=1000, clean=991))
        j = mutation.judge(self.BASE, worse_guard, {"g": "guard"})
        self.assertFalse(j["accepted"])
        self.assertIn("g: clean samples", " ".join(j["reasons"]))
        self.assertEqual(j["overall_delta"], 0.0, "the guard does not enter the mean")

    def test_finds_on_unscored_personal_data_are_reported_before_and_after(self):
        # TASK-18.2: a rule that finds passports, which no dataset scores, looked like a pure win when left out
        base = dict(self.BASE, a=Counts(tp=80, fp=20, found=60, fn=40, samples=100, clean=90, oos_found=30,
                                        oos_total=40))
        mut = dict(base, a=Counts(tp=80, fp=20, found=60, fn=40, samples=100, clean=90, oos_found=5, oos_total=40))
        self.assertEqual(mutation.judge(base, mut, {})["datasets"]["a"]["oos_found"], (30, 5))

    def test_no_change_is_accepted_with_zero_delta(self):
        j = mutation.judge(self.BASE, dict(self.BASE), {})
        self.assertTrue(j["accepted"])
        self.assertEqual(j["overall_delta"], 0.0)
        self.assertEqual(j["verdict"], "strict")

    # a: 60 of 100 found, P 0.8, F1 0.6857; one find fewer is a recall loss of 1 point
    def test_a_small_recall_loss_with_a_higher_score_passes_within_tolerance(self):
        mut = dict(self.BASE, a=Counts(tp=80, fp=0, found=59, fn=41, samples=100, clean=100))
        j = mutation.judge(self.BASE, mut, {}, recall_tolerance=0.01)
        self.assertEqual(j["verdict"], "tolerance")
        self.assertTrue(j["accepted"])
        self.assertIn("a: recall", " ".join(j["reasons"]), "the reasons still say why it is not strict")

    def test_a_recall_loss_beyond_the_tolerance_rejects(self):
        mut = dict(self.BASE, a=Counts(tp=80, fp=0, found=58, fn=42, samples=100, clean=100))
        j = mutation.judge(self.BASE, mut, {}, recall_tolerance=0.01)
        self.assertEqual(j["verdict"], "rejected")
        self.assertFalse(j["accepted"])

    def test_a_lower_score_rejects_even_within_the_recall_tolerance(self):
        mut = dict(self.BASE, a=Counts(tp=80, fp=20, found=59, fn=41, samples=100, clean=90))
        j = mutation.judge(self.BASE, mut, {}, recall_tolerance=0.01)
        self.assertEqual(j["verdict"], "rejected")

    def test_the_default_tolerance_is_half_a_point(self):
        self.assertEqual(mutation.RECALL_TOLERANCE, 0.005)
        mut = dict(self.BASE, a=Counts(tp=80, fp=0, found=59, fn=41, samples=100, clean=100))
        self.assertEqual(mutation.judge(self.BASE, mut, {})["verdict"], "rejected", "1 point is beyond the default")

    def test_a_worse_guard_rejects_within_tolerance_too(self):
        worse_guard = dict(self.BASE, g=Counts(fp=9, samples=1000, clean=991))
        self.assertEqual(mutation.judge(self.BASE, worse_guard, {"g": "guard"}, recall_tolerance=0.5)["verdict"],
                         "rejected")


if __name__ == "__main__":
    unittest.main()
