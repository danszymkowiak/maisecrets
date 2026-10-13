"""The normaliser before the shape rules (TASK-11.25): a cleaned copy of the text and a map from each of its offsets
back to the original, so a span found in the copy redacts the true text. detect.NORMALISE names the stages the plugin
ships with (TASK-44: every stage but escape); it turns
stages on. Every invisible character here is an escape."""
from __future__ import annotations

import dataclasses
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect, normalise  # noqa: E402

GHP = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
ALL = normalise.STAGES


def back(text: str, n, a: int, b: int) -> str:
    """The original text under the normalised span [a, b)."""
    s, e = n.span(a, b)
    return text[s:e]


class StageTests(unittest.TestCase):
    def check(self, stage, text, want):
        n = normalise.normalise(text, (stage,))
        self.assertEqual(n.text, want)
        if n.starts is not None:
            self.assertEqual((len(n.starts), len(n.ends)), (len(want), len(want)))
        return n

    def test_ascii_text_without_escapes_is_returned_as_is(self):
        text = "token = " + GHP + "\n"
        n = normalise.normalise(text, ALL)
        self.assertIs(n.text, text)
        self.assertEqual(n.span(3, 9), (3, 9))

    def test_invisible_characters_are_deleted(self):
        for ch in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u200e", "\u202e", "\u2066"):
            with self.subTest(ch=hex(ord(ch))):
                self.check("invisible", GHP[:10] + ch + GHP[10:], GHP)

    def test_ansi_and_osc_sequences_are_deleted(self):
        self.check("ansi", GHP[:10] + "\x1b[0m" + GHP[10:], GHP)
        self.check("ansi", "\x1b[01;31m\x1b[K" + GHP + "\x1b[m\x1b[K", GHP)
        self.check("ansi", "\x1b]8;;http://x\x07" + GHP + "\x1b]8;;\x1b\\", GHP)

    def test_a_lone_carriage_return_is_deleted_and_a_crlf_stays(self):
        self.check("cr", GHP[:10] + "\r" + GHP[10:], GHP)
        self.check("cr", "a\r\nb", "a\r\nb")

    def test_cat_grep_and_diff_gutters_are_deleted(self):
        self.check("gutter", "     1\tAPP_NAME=x\n     2\tB=y\n", "APP_NAME=x\nB=y\n")
        self.check("gutter", "src/app.py:12:name = x\nsrc/app.py-13-y\n", "name = x\ny\n")
        self.check("gutter", "@@ -1,2 +1,2 @@\n-old = 1\n+name = x\n context\n",
                   "@@ -1,2 +1,2 @@\nold = 1\nname = x\ncontext\n")

    def test_a_line_that_is_not_a_gutter_keeps_its_start(self):
        self.check("gutter", "- item one\n+ plus\n", "- item one\n+ plus\n")    # no hunk header: a list
        self.check("gutter", "key:value\n", "key:value\n")

    def test_html_entities_and_markdown_escapes_are_decoded(self):
        self.check("entity", "".join(f"&#{ord(c)};" for c in "ab") + "&amp;&#x41;", "ab&A")
        self.check("escape", "glpat\\-abc\\_def", "glpat-abc_def")

    def test_fullwidth_forms_fold_to_ascii(self):
        self.check("fullwidth", "".join(chr(ord(c) + 0xFEE0) for c in "ghp_A1"), "ghp_A1")

    def test_an_offset_maps_back_to_the_original_value(self):
        text = "x \x1b[1m" + GHP[:10] + "\u200b" + GHP[10:] + "\x1b[0m y"
        n = normalise.normalise(text, ALL)
        a = n.text.index(GHP)
        self.assertEqual(back(text, n, a, a + len(GHP)), GHP[:10] + "\u200b" + GHP[10:])

    def test_an_entity_maps_back_to_the_whole_entity(self):
        text = "v=" + "".join(f"&#{ord(c)};" for c in "abc") + ";"
        n = normalise.normalise(text, ("entity",))
        self.assertEqual(n.text, "v=abc;")
        self.assertEqual(back(text, n, 2, 5), text[2:-1])


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.rs = dataclasses.replace(detect.default_ruleset(), normalise=ALL)

    def found(self, text):
        return [(m.kind, text[m.start:m.end]) for m in detect.scan(text)]

    def test_the_shipped_stages(self):
        # TASK-44, approved 2026-10-13: every stage but escape (60 more false hits on Gretel, TASK-11.25)
        shipped = ("ansi", "cr", "invisible", "gutter", "entity", "fullwidth", "decode", "unwrap")
        self.assertEqual(detect.NORMALISE, shipped)
        self.assertEqual(detect.default_ruleset().normalise, shipped)
        self.assertEqual(self.found("t " + GHP[:10] + "\u200b" + GHP[10:]), [("github-pat", GHP[:10] + "\u200b" + GHP[10:])])

    def test_a_split_token_is_found_and_its_true_span_redacted(self):
        text = "t " + GHP[:10] + "\u200b" + GHP[10:] + " end"
        hits = detect.scan(text, ruleset=self.rs)
        self.assertEqual(len(hits), 1)
        self.assertEqual(text[hits[0].start:hits[0].end], GHP[:10] + "\u200b" + GHP[10:])
        self.assertEqual(hits[0].value, text[hits[0].start:hits[0].end])

    def test_a_hit_of_the_raw_text_wins_over_the_normalised_one(self):
        text = GHP + " and " + GHP[:10] + "\x1b[0m" + GHP[10:]
        spans = [(m.start, m.end) for m in detect.scan(text, ruleset=self.rs)]
        self.assertEqual(spans[0], (0, len(GHP)))
        self.assertEqual(len(spans), 2)


if __name__ == "__main__":
    unittest.main()
