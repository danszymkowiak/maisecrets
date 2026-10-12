"""Kingfisher's two placeholder exclusions (TASK-19.6) are already the detector's behaviour, and this test keeps them:
a PEM block with almost nothing between BEGIN and END is no private key, and a MongoDB URI whose password is only a
variable reference ($(NAME), ${NAME}, $NAME, {{ name }}) holds no secret. The real ones are still found.

Run: python3 -m unittest tests.test_placeholder_filters -v
"""
from __future__ import annotations

import os
import random
import string
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect  # noqa: E402

_R = random.Random(196)
B64 = string.ascii_letters + string.digits + "+/"
# built from pieces: a literal PEM frame in the tree is what the repository's own scan flags
BEGIN, END = "-----BEGIN " + "PRIVATE KEY-----", "-----END " + "PRIVATE KEY-----"


def secrets(text: str) -> list[str]:
    return [m.kind for m in detect.scan(text) if m.type == "SECRET"]


class PlaceholderFilterTests(unittest.TestCase):
    def test_a_short_pem_block_is_no_private_key(self):
        for body in ("MIIEvQIBADAN", "...", "<your key here>"):
            with self.subTest(body=body):
                self.assertEqual(secrets(f"{BEGIN}\n{body}\n{END}"), [])

    def test_a_real_pem_block_is_found(self):
        body = "\n".join("".join(_R.choice(B64) for _ in range(64)) for _ in range(6))
        self.assertIn("private-key", secrets(f"{BEGIN}\n{body}\n{END}"))

    def test_a_mongodb_password_that_is_a_variable_is_no_secret(self):
        for ref in ("$(MONGO_PASSWORD)", "${MONGO_PASSWORD}", "$MONGO_PASSWORD", "{{ mongo_password }}"):
            with self.subTest(ref=ref):
                self.assertEqual(secrets(f"mongodb://admin:{ref}@db.example.org:27017/app"), [])

    def test_a_literal_mongodb_password_is_found(self):
        pw = "".join(_R.choice(string.ascii_letters + string.digits) for _ in range(16))
        hits = [m for m in detect.scan(f"mongodb://admin:{pw}@db.example.org:27017/app") if m.type == "SECRET"]
        self.assertTrue(any(pw in m.value for m in hits))


if __name__ == "__main__":
    unittest.main()
