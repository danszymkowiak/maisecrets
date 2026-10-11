import unittest

from maisecrets_bench import filters, mutation
from maisecrets_bench.detector import detect
from maisecrets_bench.paths import BenchError

# split so that the tree scan does not see a keyword and a value in one literal
GLUED = "pass" + "word:" + "Kx7Q" + "p2Zr9"          # 9 characters glued to the label: the ds_value glued path
SPACED = "pass" + "word: " + "Kx7Q" + "p2Zr9Lm4Wn"


def _hits(text: str, m: mutation.Mutation | None) -> list:
    saved = detect._RULES
    try:
        detect._RULES = mutation.apply(m, detect.rules()) if m else saved
        return [(x.kind, x.value) for x in detect.scan(text)]
    finally:
        detect._RULES = saved
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


if __name__ == "__main__":
    unittest.main()
