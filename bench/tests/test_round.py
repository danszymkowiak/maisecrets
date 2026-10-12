"""An agent round (docs/BENCHMARK.md, Dev and check): the brief holds what an agent may read (dev scores, the rules
with the most false alarms and their definitions, masked errors, the mutation format); judging runs a proposal on
dev and on check, and only the totals of check come back.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import detector, round as rnd, run, schema
from maisecrets_bench.mutation import Mutation
from maisecrets_bench.schema import Sample, Span

MAIL = "zq.tester@example-mail.org"
PHONE = "+49 30 9876 5432"


class RuleIndexTests(unittest.TestCase):
    def test_every_rule_is_described_by_id(self):
        idx = detector.rule_index()
        self.assertIn("us-bank", idx)
        self.assertIn("email", idx)
        self.assertIn("regex", idx["email"])
        self.assertEqual(idx["email"]["type"], "EMAIL")


class RoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        m = f"Write to {MAIL} today."
        rows = [Sample("toy", f"d{i}", f"g{i}", "de", f"Call {PHONE} now.", [], "dev") for i in range(3)]
        rows += [Sample("toy", f"c{i}", f"h{i}", "de", f"Call {PHONE} now.", [], "check") for i in range(2)]
        rows += [Sample("toy", "m", "gm", "en", m, [Span(9, 9 + len(MAIL), "EMAIL", "EMAIL", "pos")], "dev")]
        schema.write(rows, d / "toy.parquet")
        (d / "manifest.json").write_text(json.dumps({"datasets": {"toy": {"version": "t1"}}}))
        run.run(d, ["toy"], d / "run", jobs=2)
        cls.d = d

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_brief_names_the_false_alarm_rule_with_its_definition_and_no_value(self):
        text = rnd.brief(self.d / "run", self.d)
        self.assertIn("phone", text)
        self.assertIn("regex", text)
        self.assertIn("[[change]]", text, "the mutation format")
        for v in (MAIL, PHONE, "9876"):
            self.assertNotIn(v, text)

    def test_the_brief_holds_dev_scores_only(self):
        text = rnd.brief(self.d / "run", self.d)
        self.assertIn("dev", text)
        self.assertNotIn("check score", text)

    def test_a_proposal_is_judged_on_dev_and_on_check(self):
        m = Mutation("no phone", "", [{"op": "disable", "rule": "phone"}])
        (r,) = rnd.judge([m], self.d / "run", self.d, {}, jobs=2)
        self.assertTrue(r["dev"]["accepted"])
        self.assertTrue(r["check"]["accepted"])
        self.assertTrue(r["accepted"])
        self.assertEqual(r["verdict"], "accepted", "fewer false positives, every floor held")
        self.assertEqual(r["dev"]["old_verdict"], "strict")
        self.assertLess(r["dev"]["objective_delta"], 0)
        self.assertNotIn("datasets", r["check"], "check gives totals only")
        self.assertNotIn("floors", r["check"])


if __name__ == "__main__":
    unittest.main()
