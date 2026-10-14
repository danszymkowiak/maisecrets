import unittest
from collections import defaultdict

from maisecrets_bench.adapters.datasets import synthetic
from maisecrets_bench.adapters.compose import load_labels as load
from maisecrets_bench.domain.samples import OUT_OF_SCOPE


def _build(n=20, seed=synthetic.SEED):
    return list(synthetic.samples(load("synthetic"), per_template=n, seed=seed))


class SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = _build()

    def test_the_same_seed_builds_the_same_text_and_spans(self):
        again = _build()
        self.assertEqual([(s.text, s.spans) for s in self.rows], [(s.text, s.spans) for s in again])
        self.assertNotEqual([s.text for s in _build(seed=1)], [s.text for s in self.rows])

    def test_every_template_has_pos_and_neg_spans_inside_its_text(self):
        kinds = defaultdict(set)
        for s in self.rows:
            for sp in s.spans:
                self.assertTrue(0 <= sp.start < sp.end <= len(s.text), s.sample_id)
                self.assertEqual(s.text[sp.start:sp.end].strip(), s.text[sp.start:sp.end], "no blank at an edge")
                kinds[s.sample_id.split(":")[0]].add(sp.gold)
        self.assertEqual(set(kinds), set(synthetic.TEMPLATES))
        for name, golds in kinds.items():
            self.assertEqual(golds, {"pos", "neg"}, name)

    def test_negatives_are_out_of_scope_and_positives_are_types(self):
        for s in self.rows:
            for sp in s.spans:
                self.assertEqual(sp.maisecrets_type == OUT_OF_SCOPE, sp.gold == "neg", sp.label)

    def test_spans_do_not_overlap(self):
        for s in self.rows:
            ends = sorted((sp.start, sp.end) for sp in s.spans)
            for (a, b), (c, d) in zip(ends, ends[1:]):
                self.assertLessEqual(b, c, s.sample_id)

    def test_the_version_names_seed_and_size(self):
        self.assertIn(f"seed{synthetic.SEED}-n{synthetic.PER_TEMPLATE}-", synthetic.version())


if __name__ == "__main__":
    unittest.main()
