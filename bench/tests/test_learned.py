import random
import unittest

from maisecrets_bench.adapters.plugin import learned


class FeatureTests(unittest.TestCase):
    def test_one_fixed_length_vector_of_numbers(self):
        value = "q8Zt3" + "LmR0pWvX2c9"
        text = "api_" + 'key = "' + value + '"\n'   # in pieces: the tree scan would flag the literal
        start = text.index(value)
        f = learned.features(value, text, start, start + len(value), "generic-api-key")
        self.assertEqual(len(f), len(learned.NAMES))
        self.assertTrue(all(isinstance(x, float) for x in f))

    def test_the_label_class_and_the_rule_are_one_hot(self):
        text = "token_count: 12345678\n"
        start = text.index("1")
        f = dict(zip(learned.NAMES, learned.features("12345678", text, start, start + 8, "ds-keyword-colon")))
        self.assertEqual(f["label_negative"], 1.0)
        self.assertEqual(f["label_strong"], 0.0)
        self.assertEqual(f["rule:ds-keyword-colon"], 1.0)
        self.assertEqual(f["rule:generic-api-key"], 0.0)


class TrainTests(unittest.TestCase):
    def test_logistic_regression_separates_a_separable_set(self):
        r = random.Random(3)
        xs = [[r.gauss(1, 0.3), r.gauss(0, 1)] for _ in range(200)] + [[r.gauss(-1, 0.3), r.gauss(0, 1)]
                                                                       for _ in range(200)]
        ys = [1] * 200 + [0] * 200
        model = learned.train(xs, ys, epochs=200)
        right = sum((learned.prob(model, x) > 0.5) == bool(y) for x, y in zip(xs, ys))
        self.assertGreater(right, 390)

    def test_the_threshold_keeps_every_find_it_was_given(self):
        model = learned.train([[1.0], [0.5], [-1.0], [-0.2]], [1, 1, 0, 0], epochs=100)
        t = learned.keep_all_threshold(model, [[1.0], [0.5]])
        self.assertTrue(all(learned.prob(model, x) >= t for x in ([1.0], [0.5])))

    def test_a_model_round_trips_through_its_table(self):
        model = learned.train([[1.0, 2.0], [-1.0, 0.0]], [1, 0], epochs=10)
        back = learned.from_table(learned.to_table(model, 0.1, ["a", "b"]))
        self.assertEqual(back[0], model)
        self.assertEqual(back[1], 0.1)


if __name__ == "__main__":
    unittest.main()
