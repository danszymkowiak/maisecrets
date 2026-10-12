"""Our own generators write only valid values (TASK-30): every positive of findocs and of the synthetic tool output
passes the validity rules of valid gold as it stands, with nothing trimmed, made uncertain, negative or retyped. A
generator that invents a reserved area code ((494) ...) would teach the rules a shape no real number has."""
from __future__ import annotations

import unittest

from maisecrets_bench import validgold
from maisecrets_bench.adapters import findocs, synthetic
from maisecrets_bench.labels import load


class GeneratedGoldTests(unittest.TestCase):
    def assert_all_valid(self, rows):
        _, stats = validgold.mark(rows)
        for ds, types in stats.items():
            for t, c in types.items():
                with self.subTest(dataset=ds, type=t):
                    self.assertEqual((c["invalid"], c["trimmed"], c["negative"], c["retyped"]), (0, 0, 0, 0), c)

    def test_findocs(self):
        self.assert_all_valid(list(findocs.samples(load("findocs"))))

    def test_synthetic(self):
        self.assert_all_valid(list(synthetic.samples(load("synthetic"))))


if __name__ == "__main__":
    unittest.main()
