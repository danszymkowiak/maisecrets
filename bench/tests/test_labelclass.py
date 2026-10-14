"""The label before a value, by word sets (TASK-11.23): strong, weak, negative or none.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench.domain import labelclass


class WordTests(unittest.TestCase):
    def test_labels_split_into_lowercase_words(self):
        self.assertEqual(labelclass.words("clientSecret"), ["client", "secret"])
        self.assertEqual(labelclass.words("AWS_SECRET_ACCESS_KEY"), ["aws", "secret", "access", "key"])
        self.assertEqual(labelclass.words("config.api-key"), ["config", "api", "key"])


class ClassTests(unittest.TestCase):
    def test_strong_labels(self):
        for label in ("password", "DB_PASSWORD", "api_key", "apiKey", "client_secret", "GITHUB_TOKEN", "passphrase",
                      "private_key", "AWS_SECRET_ACCESS_KEY", "authToken"):
            self.assertEqual(labelclass.classify(label), "strong", label)

    def test_weak_labels(self):
        for label in ("key", "auth", "credential", "credentials", "signing_key", "pass"):
            self.assertEqual(labelclass.classify(label), "weak", label)

    def test_every_negative_sibling_blocks(self):
        for word in labelclass.NEGATIVE_LAST:
            self.assertEqual(labelclass.classify(f"token_{word}"), "negative", word)
        for word in labelclass.NEGATIVE_WHOLE:
            self.assertEqual(labelclass.classify(word), "negative", word)

    def test_the_listed_siblings_are_in_the_table(self):
        for word in ("count", "max", "hash", "path", "url", "length", "file", "name", "type"):
            self.assertIn(word, labelclass.NEGATIVE_LAST)
        for word in ("id", "passport", "passage"):     # measured: mostly real values behind them
            self.assertNotIn(word, labelclass.NEGATIVE_LAST | labelclass.NEGATIVE_WHOLE)
        for word in ("tokenizer", "secretary", "passwordless"):
            self.assertIn(word, labelclass.NEGATIVE_WHOLE)

    def test_a_secret_word_after_a_negative_one_is_strong(self):
        self.assertEqual(labelclass.classify("hash_password"), "strong", "the last word decides")
        self.assertEqual(labelclass.classify("max_token"), "strong")

    def test_no_secret_word_is_none(self):
        self.assertEqual(labelclass.classify("username"), "none")
        self.assertEqual(labelclass.classify(""), "none")


if __name__ == "__main__":
    unittest.main()
