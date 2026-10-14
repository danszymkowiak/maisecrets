import base64
import unittest

from maisecrets_bench.domain import perturb
from maisecrets_bench.domain.samples import OUT_OF_SCOPE, Sample, Span

MAIL = "zq.tester" + "@" + "mailhost-sample.com"


def _sample(text, spans):
    return Sample("toy", "a", "a", "en", text, spans, "dev")


class TransformTests(unittest.TestCase):
    def test_every_listed_transform_exists_and_none_is_the_identity(self):
        self.assertEqual(set(perturb.TRANSFORMS), {"none", "zero_width", "soft_hyphen", "fullwidth", "homoglyph",
                                                   "ansi_reset", "cr", "wrap", "base64", "hex", "entity", "escape",
                                                   "truncation"})
        self.assertEqual(perturb.TRANSFORMS["none"](MAIL), MAIL)

    def test_the_transforms_do_what_their_names_say(self):
        t = perturb.TRANSFORMS
        self.assertIn("​", t["zero_width"](MAIL))
        self.assertIn("­", t["soft_hyphen"](MAIL))
        self.assertEqual(t["fullwidth"]("a1")[0], "ａ")
        self.assertIn("а", t["homoglyph"]("tata"), "Cyrillic a")
        self.assertIn("\x1b[0m", t["ansi_reset"](MAIL))
        self.assertIn("\r", t["cr"](MAIL))
        self.assertIn("\n", t["wrap"](MAIL))
        self.assertEqual(base64.b64decode(t["base64"](MAIL)).decode(), MAIL)
        self.assertEqual(bytes.fromhex(t["hex"](MAIL)).decode(), MAIL)
        self.assertTrue(t["entity"]("ab") == "&#97;&#98;")
        self.assertEqual(t["escape"]("a_b.c"), "a\\_b\\.c")
        self.assertTrue(MAIL.startswith(t["truncation"](MAIL).rstrip("…")))
        self.assertLess(len(t["truncation"](MAIL)), len(MAIL))


class RewriteTests(unittest.TestCase):
    def test_in_scope_positives_are_rewritten_and_their_spans_follow(self):
        text = f"to {MAIL} and {MAIL} done"
        a = text.index(MAIL)
        b = text.index(MAIL, a + 1)
        s = _sample(text, [Span(a, a + len(MAIL), "email", "EMAIL", "pos"),
                           Span(b, b + len(MAIL), "x", OUT_OF_SCOPE, "pos"),
                           Span(len(text) - 4, len(text), "w", OUT_OF_SCOPE, "neg")])
        out = perturb.rewrite(s, perturb.TRANSFORMS["base64"])
        enc = base64.b64encode(MAIL.encode()).decode()
        self.assertEqual(out.text, f"to {enc} and {MAIL} done")
        self.assertEqual([out.text[sp.start:sp.end] for sp in out.spans], [enc, MAIL, "done"])

    def test_a_sample_with_overlapping_positives_is_left_out(self):
        s = _sample("abcdef", [Span(0, 4, "x", "EMAIL", "pos"), Span(2, 6, "y", "EMAIL", "pos")])
        self.assertIsNone(perturb.rewrite(s, perturb.TRANSFORMS["hex"]))

    def test_the_pick_is_deterministic_and_takes_samples_with_in_scope_positives(self):
        rows = [Sample("toy", str(i), str(i), "en", "x" * 10,
                       [Span(0, 3, "e", "EMAIL" if i % 2 else OUT_OF_SCOPE, "pos")], "dev") for i in range(40)]
        a, b = perturb.pick(rows, 5), perturb.pick(list(reversed(rows)), 5)
        self.assertEqual([s.sample_id for s in a], [s.sample_id for s in b])
        self.assertTrue(all(int(s.sample_id) % 2 for s in a))


if __name__ == "__main__":
    unittest.main()
