"""Decode-and-rescan (TASK-11.26): the normaliser's decode stage replaces a base64 or hex run whose bytes are text by
that text, so the shape rules see a value encoded inside it; a hit there redacts the whole encoded run. Off by default
like every stage; bounded by depth, run length, decoded bytes, candidate count and a time slice."""
from __future__ import annotations

import base64
import dataclasses
import gzip
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import decode, detect, normalise  # noqa: E402

GHP = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
MAIL = "jane.roe@mailbox.org"


def b64(s: str | bytes) -> str:
    return base64.b64encode(s.encode() if isinstance(s, str) else s).decode()


class DecodeTests(unittest.TestCase):
    def test_base64_of_text_is_decoded(self):
        self.assertEqual(decode.decode_run(b64("token " + GHP)), "token " + GHP)

    def test_urlsafe_base64_without_padding_is_decoded(self):
        raw = '{"email":"' + MAIL + '","sub":"x>>?"}'
        enc = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        self.assertEqual(decode.decode_run(enc), raw)

    def test_hex_of_text_is_decoded(self):
        self.assertEqual(decode.decode_run(("secret " + GHP).encode().hex()), "secret " + GHP)

    def test_random_bytes_are_not_text(self):
        self.assertIsNone(decode.decode_run(b64(bytes(range(256))[:48])))
        self.assertIsNone(decode.decode_run("sha512-" + b64(os.urandom(64))))

    def test_a_digest_in_hex_is_not_text(self):
        self.assertIsNone(decode.decode_run("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))

    def test_an_identifier_that_looks_like_base64_is_left_alone(self):
        self.assertIsNone(decode.decode_run("ThisIsAVeryLongCamelCaseIdentifierName"))

    def test_gzip_inside_base64_is_decoded_at_depth_two(self):
        enc = b64(gzip.compress(("password=" + GHP).encode()))
        self.assertEqual(decode.decode_run(enc), "password=" + GHP)

    def test_base64_inside_base64_is_decoded_at_depth_two_and_no_deeper(self):
        two = b64(b64("key " + GHP))
        self.assertEqual(decode.decode_run(two), "key " + GHP)
        three = b64(two)
        self.assertNotIn(GHP, decode.decode_run(three) or "")

    def test_a_run_longer_than_the_cap_is_not_decoded(self):
        self.assertIsNone(decode.decode_run(b64("x" * (decode.MAX_RUN))))


class StageTests(unittest.TestCase):
    def test_the_stage_maps_a_decoded_value_back_to_the_whole_run(self):
        enc = b64("token " + GHP)
        text = "data:\n  config: " + enc + "\n"
        n = normalise.normalise(text, ("decode",))
        a = n.text.index(GHP)
        s, e = n.span(a, a + len(GHP))
        self.assertEqual(text[s:e], enc)

    def test_text_without_an_encoded_run_is_returned_as_is(self):
        text = "plain words and " + GHP + " and a digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b"
        self.assertIs(normalise.normalise(text, ("decode",)).text, text)

    def test_a_one_megabyte_blob_stays_within_the_time_slice(self):
        # 1 MiB of base64 that decodes to text. A text the stage changes also pays for the normaliser's offset map,
        # per character like every stage (bench/normtime.py measures that)
        blob = b64(("lorem ipsum " * 90_000)[:786_432])
        text = "payload: " + blob + "\n"
        t0 = time.perf_counter()
        normalise.normalise(text, ("decode",))
        self.assertLess(time.perf_counter() - t0, decode.TIME_SLICE + 0.05)

    def test_the_candidate_and_byte_caps_bound_the_work(self):
        text = "\n".join("k: " + b64(f"token {i} " + GHP) for i in range(decode.MAX_CANDIDATES + 20))
        n = normalise.normalise(text, ("decode",))
        self.assertLessEqual(n.text.count(GHP), decode.MAX_CANDIDATES)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.rs = dataclasses.replace(detect.default_ruleset(), normalise=("decode",))

    def test_off_by_default(self):
        text = "auth: " + b64("contact " + MAIL)
        self.assertNotIn("decode", detect.NORMALISE)
        self.assertEqual([m for m in detect.scan(text) if m.type == "EMAIL"], [])

    def test_an_email_inside_a_jwt_like_payload_redacts_the_encoded_run(self):
        enc = b64('{"email":"' + MAIL + '"}')
        text = "payload " + enc + " end"
        hits = [m for m in detect.scan(text, ruleset=self.rs) if m.type == "EMAIL"]
        self.assertEqual([(text[m.start:m.end]) for m in hits], [enc])

    def test_a_token_encoded_in_a_config_value_is_found(self):
        enc = b64(GHP)
        text = "settings:\n  blob: " + enc + "\n"

        def covers(hits):
            return any(m.start <= text.index(enc) and text.index(enc) + len(enc) <= m.end for m in hits)
        self.assertFalse(covers(detect.scan(text)), "the rules alone miss it")
        self.assertTrue(covers(detect.scan(text, ruleset=self.rs)))


if __name__ == "__main__":
    unittest.main()
