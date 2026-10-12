import unittest

from maisecrets_bench import filters, mutation
from maisecrets_bench.detector import detect
from maisecrets_bench.paths import BenchError

# split so that the tree scan does not see a keyword and a value in one literal
GLUED = "pass" + "word:" + "Kx7Q" + "p2Zr9"          # 9 characters glued to the label: the ds_value glued path
SPACED = "pass" + "word: " + "Kx7Q" + "p2Zr9Lm4Wn"


def _hits(text: str, m: mutation.Mutation | None) -> list:
    try:
        rs = mutation.ruleset(m, detect.default_ruleset()) if m else None
        return [(x.kind, x.value) for x in detect.scan(text, ruleset=rs)]
    finally:
        filters.ACTIVE.clear()


def _with(rule: str, name: str) -> mutation.Mutation:
    return mutation.Mutation("x", "", [{"op": "set", "rule": rule, "filter": name}])


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.seen = []

        def spy(value, text, start, end):
            self.seen.append((value, text[start:end], text[:start]))
            return True
        filters.FILTERS["bench:test_spy"] = spy
        self.addCleanup(filters.FILTERS.pop, "bench:test_spy")

    def test_a_keeping_filter_leaves_a_glued_value_a_hit_and_sees_the_label_before_it(self):
        base = _hits(GLUED, None)
        self.assertEqual([k for k, _ in base], ["ds-keyword-colon"], "the glued value is a hit without a filter")
        self.assertEqual(_hits(GLUED, _with("ds-keyword-colon", "bench:test_spy")), base)
        value, span, before = self.seen[0]
        self.assertEqual(value, span, "start and end point at the value")
        self.assertTrue(before.lower().endswith("word:"), "the filter can read the label")

    def test_a_dropping_filter_removes_every_hit_of_its_rule(self):
        self.assertTrue(_hits(SPACED, None))
        self.assertEqual([h for h in _hits(SPACED, _with("ds-keyword-colon", "bench:drop_all"))
                          if h[0] == "ds-keyword-colon"], [])

    def test_the_rule_s_own_validator_runs_first(self):
        # a 3-character value fails ds_value: the filter is never asked
        _hits("pass" + "word: abc", _with("ds-keyword-colon", "bench:test_spy"))
        self.assertEqual(self.seen, [])

    def test_an_unknown_filter_is_named(self):
        with self.assertRaisesRegex(BenchError, "bench:nope"):
            mutation.validate(_with("ds-keyword-colon", "bench:nope"))

    def test_a_filter_on_a_new_rule(self):
        m = mutation.Mutation("x", "", [{"op": "add", "id": "zz-test", "type": "SECRET", "regex": "zzq[0-9]{4}",
                                         "filter": "bench:drop_all"}])
        mutation.validate(m)
        self.assertNotIn("zz-test", [k for k, _ in _hits("x zzq1234 y", m)])


HEX40 = "3f" * 20
HEX24 = "a1" * 12


class DigestFilterTests(unittest.TestCase):
    """TASK-11.20: a digest, a prefixed digest or an ObjectId is dropped only by what the text says it is."""

    def keep(self, name: str, text: str, value: str) -> bool:
        start = text.index(value)
        return filters.FILTERS[name](value, text, start, start + len(value))

    def test_a_hex_value_behind_a_digest_label_is_dropped(self):
        for label in ("checksum = ", "sha256: ", "commit_hash=", "\"etag\": \"", "git rev ", "md5sum "):
            self.assertFalse(self.keep("bench:digest_label", label + HEX40, HEX40), label)

    def test_a_hex_value_behind_a_secret_label_or_of_another_length_stays(self):
        self.assertTrue(self.keep("bench:digest_label", "api_" + "key = " + HEX40, HEX40))
        self.assertTrue(self.keep("bench:digest_label", "checksum = " + HEX40[:30], HEX40[:30]))
        self.assertTrue(self.keep("bench:digest_label", "checksum = Zq" + HEX40[2:], "Zq" + HEX40[2:]))

    def test_a_prefixed_digest_is_dropped(self):
        for text, value in (("sha256:" + HEX40 * 2, HEX40 * 2), ("x sha512-QUJD+/ab==", "sha512-QUJD+/ab=="),
                            ("mod v1.2.0 h1:QUJDREVG+/abc=", "h1:QUJDREVG+/abc=")):
            self.assertFalse(self.keep("bench:digest_prefix", text, value), text)
        self.assertTrue(self.keep("bench:digest_prefix", "tok" + "en: " + HEX40, HEX40))

    def test_an_object_id_is_dropped_by_its_call_or_its_label(self):
        self.assertFalse(self.keep("bench:object_id", 'ObjectId("' + HEX24 + '")', HEX24))
        self.assertFalse(self.keep("bench:object_id", '"_id": "' + HEX24 + '"', HEX24))
        self.assertTrue(self.keep("bench:object_id", "sec" + "ret: " + HEX24, HEX24))

    def test_the_combined_filter_drops_what_any_of_them_drops(self):
        self.assertFalse(self.keep("bench:digest_any", "checksum = " + HEX40, HEX40))
        self.assertFalse(self.keep("bench:digest_any", 'ObjectId("' + HEX24 + '")', HEX24))
        self.assertTrue(self.keep("bench:digest_any", "pass" + "word = " + HEX40, HEX40))


class WordlikeFilterTests(unittest.TestCase):
    """TASK-11.22, with a word list of its own (filters read MAISECRETS_BENCH_WORDS)."""

    def setUp(self):
        import os
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "words")
        with open(p, "w", encoding="utf-8") as f:
            f.write("connection\ntimeout\npool\nsize\n")
        saved = os.environ.get("MAISECRETS_BENCH_WORDS")
        os.environ["MAISECRETS_BENCH_WORDS"] = p
        filters._WORDS.clear()

        def restore():
            filters._WORDS.clear()
            if saved is None:
                os.environ.pop("MAISECRETS_BENCH_WORDS", None)
            else:
                os.environ["MAISECRETS_BENCH_WORDS"] = saved
        self.addCleanup(restore)

    def keep(self, name, text, value):
        start = text.index(value)
        return filters.FILTERS[name](value, text, start, start + len(value))

    def test_a_word_made_value_is_dropped_and_a_random_one_stays(self):
        self.assertFalse(self.keep("bench:wordlike_75", "api_" + "key = connectionTimeout", "connectionTimeout"))
        self.assertTrue(self.keep("bench:wordlike_75", "api_" + "key = Xq7vR2" + "mK9pLw", "Xq7vR2" + "mK9pLw"))

    def test_a_strong_label_keeps_a_word_made_value(self):
        self.assertTrue(self.keep("bench:wordlike_75", "pass" + "word = poolsize", "poolsize"))


if __name__ == "__main__":
    unittest.main()


class EntropyCharsetFilterTests(unittest.TestCase):
    """TASK-11.21: one raw-entropy threshold per charset, chosen on dev (curves of 20261012-194832)."""

    def test_a_value_keeps_when_its_entropy_reaches_its_charset_threshold(self):
        keep = filters.FILTERS["bench:entropy_charset"]
        self.assertTrue(keep("a1B2c3D4e5F6g7H8i9J0kLmN", "", 0, 0))      # base62, high entropy
        self.assertFalse(keep("aaaaaaaabbbbbbbb", "", 0, 0))              # hex alphabet? no: base62, low entropy
        self.assertFalse(keep("abab-abab-abab-abab!!", "", 0, 0))         # printable, below 3.594

    def test_every_charset_has_a_threshold(self):
        from maisecrets_bench import entropy
        self.assertEqual(set(filters.ENTROPY_BY_CHARSET),
                         {"hex", "base32", "base62", "base64", "base64url", "printable"})
        self.assertTrue(all(entropy.charset(v) in filters.ENTROPY_BY_CHARSET for v in ("ab12", "AB==", "a_b-")))
