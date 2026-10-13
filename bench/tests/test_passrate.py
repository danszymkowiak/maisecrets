import unittest

from maisecrets_bench import passrate
from maisecrets_bench.schema import Sample, Span


def _sample(sid, text, spans):
    return Sample(dataset="d", sample_id=sid, group_id=sid, language="en", text=text, spans=spans)


class PassRateTests(unittest.TestCase):
    def setUp(self):
        text = "NIF 12345678Z and 12345678A, ref 87654321A"
        self.samples = {("d", "s1"): _sample("s1", text, [
            Span(4, 13, "national_id", "OUT_OF_SCOPE", "pos"),
            Span(18, 27, "national_id", "OUT_OF_SCOPE", "pos"),
            Span(33, 42, "ref", "OUT_OF_SCOPE", "neg"),
        ])}
        self.dets = [
            {"dataset": "d", "sample_id": "s1", "start": 4, "end": 13, "rule": "es-nif"},
            {"dataset": "d", "sample_id": "s1", "start": 18, "end": 27, "rule": "es-nif"},
            {"dataset": "d", "sample_id": "s1", "start": 33, "end": 42, "rule": "es-nif"},
            {"dataset": "d", "sample_id": "s1", "start": 0, "end": 3, "rule": "email"},
        ]

    def test_counts_hits_on_gold_and_off_it_and_which_pass(self):
        rows = passrate.table(self.samples, self.dets, {"es-nif": "bench:es_nif"})
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r.rule, r.dataset, r.validator), ("es-nif", "d", "bench:es_nif"))
        self.assertEqual((r.gold, r.gold_pass), (2, 1), "12345678Z passes, 12345678A does not")
        self.assertEqual((r.other, r.other_pass), (1, 0), "a hit on a neg span is not on gold")
        self.assertEqual(r.labels, {"national_id": 2})

    def test_a_rule_variant_counts_under_its_rule(self):
        dets = [dict(d, rule="es-nif#1") if d["rule"] == "es-nif" else d for d in self.dets]
        self.assertEqual(passrate.table(self.samples, dets, {"es-nif": "bench:es_nif"})[0].gold, 2)

    def test_the_report_prints_counts_and_labels_never_a_value(self):
        text = passrate.report(passrate.table(self.samples, self.dets, {"es-nif": "bench:es_nif"}), "run-x")
        self.assertIn("es-nif", text)
        self.assertIn("50.0%", text)
        self.assertIn("national_id", text)
        self.assertNotIn("12345678", text)

    def test_a_rule_without_a_hit_is_listed_as_not_testable(self):
        text = passrate.report(passrate.table(self.samples, self.dets, {"es-nif": "bench:es_nif",
                                                                         "pl-pesel": "bench:es_nif"}), "run-x")
        self.assertIn("pl-pesel", text)
        self.assertIn("No hit", text)


if __name__ == "__main__":
    unittest.main()
