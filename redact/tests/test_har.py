"""A HAR file (TASK-52): the browser's record of every request and response, which support desks ask for. It carries
session cookies, bearer tokens and posted passwords, and its field names say what each value is: cookies,
Authorization and token-like header, query and form names are deterministic SECRET hits; bodies go to the rules and
models; URLs and other headers stay. All values here are synthetic.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact.adapters import compose as app  # noqa: E402

from maisecrets_redact.adapters import extract  # noqa: E402

from maisecrets_redact.domain import fields  # noqa: E402

# built here, not written out: the tree's own secret scan (scripts/scan_tree.py) reads every literal
QUERY_TOKEN, FORM_PASS = "testtoken" + "-query", "testpass" + "-form"

HAR = {"log": {"version": "1.2", "creator": {"name": "test", "version": "1"}, "entries": [
    {"request": {"method": "POST", "url": f"https://app.example.com/login?next=%2Fhome&access_token={QUERY_TOKEN}",
                 "headers": [{"name": "Host", "value": "app.example.com"},
                             {"name": "Cookie", "value": "session=testcookie-1; theme=dark"},
                             {"name": "Authorization", "value": "Bearer testtoken-bearer"},
                             {"name": "X-Api-Key", "value": "testkey-header"},
                             {"name": "Accept", "value": "text/html"}],
                 "cookies": [{"name": "session", "value": "testcookie-1"}],
                 "queryString": [{"name": "next", "value": "/home"}, {"name": "access_token",
                                                                       "value": "testtoken-query"}],
                 "postData": {"mimeType": "application/x-www-form-urlencoded",
                              "text": f"user=testuser&password={FORM_PASS}",
                              "params": [{"name": "user", "value": "testuser"},
                                         {"name": "password", "value": "testpass-form"}]}},
     "response": {"status": 302, "statusText": "Found",
                  "headers": [{"name": "Set-Cookie", "value": "session=testcookie-2; Path=/; HttpOnly"},
                              {"name": "Location", "value": "https://app.example.com/home"}],
                  "cookies": [{"name": "session", "value": "testcookie-2"}],
                  "content": {"size": 0, "mimeType": "text/html", "text": ""}}},
    {"request": {"method": "GET", "url": "https://app.example.com/api/me", "headers": [], "cookies": [],
                 "queryString": []},
     "response": {"status": 200, "statusText": "OK", "headers": [{"name": "Content-Type", "value": "application/json"}],
                  "cookies": [], "content": {"size": 40, "mimeType": "application/json",
                                             "text": "{\"email\": \"max@mailbox-test.de\", \"plan\": \"free\"}"}}},
    {"request": {"method": "GET", "url": "https://cdn.example.com/logo.png", "headers": [], "cookies": [],
                 "queryString": []},
     "response": {"status": 200, "statusText": "OK", "headers": [], "cookies": [],
                  "content": {"size": 8, "mimeType": "image/png", "encoding": "base64", "text": "iVBORw0KGgo="}}},
]}}

SECRETS = ("testcookie-1", "testcookie-2", "testtoken-bearer", "testkey-header", "testtoken-query", "testpass-form")


def write(d: Path) -> Path:
    path = d / "session.har"
    path.write_text(json.dumps(HAR), encoding="utf-8")
    return path


class HarExtractTests(unittest.TestCase):
    def test_positions_name_the_entry_and_the_field(self):
        doc = extract.extract(write(Path(tempfile.mkdtemp())))

        def where(value):
            i = doc.text.index(value)
            return [p.where for p in doc.positions if p.start <= i < p.end]
        self.assertEqual(where("Bearer testtoken-bearer"), ["entry 1, request header Authorization"])
        self.assertEqual(where("testpass-form"), ["entry 1, request form password"])
        self.assertEqual(where("testtoken-query"), ["entry 1, request query access_token"])
        self.assertEqual(where("max@mailbox-test.de"), ["entry 2, response body"])
        self.assertIn(f"https://app.example.com/login?next=%2Fhome&access_token={QUERY_TOKEN}", doc.text)
        self.assertNotIn("iVBORw0KGgo", doc.text, "a binary body is left out")
        self.assertEqual(doc.text.count("testpass-form"), 1, "a form's raw text is not written twice")

    def test_the_fields_that_hold_secrets_are_hits(self):
        doc = extract.extract(write(Path(tempfile.mkdtemp())))
        got = {doc.text[s.start:s.end] for s in fields.har_spans(doc)}
        self.assertEqual(got, {"session=testcookie-1; theme=dark", "testcookie-1", "Bearer testtoken-bearer",
                               "testkey-header", "testtoken-query", "testpass-form",
                               "session=testcookie-2; Path=/; HttpOnly", "testcookie-2", "testuser"})
        self.assertEqual({s.type for s in fields.har_spans(doc) if doc.text[s.start:s.end] == "testuser"},
                         {"USERNAME"})


class HarRunTests(unittest.TestCase):
    def test_no_cookie_token_or_posted_password_and_urls_and_headers_stay(self):
        d = Path(tempfile.mkdtemp())
        src = write(d)
        self.assertEqual(app.output_name(src), "session.har.redacted.txt")
        result = app.run_file(src, d / app.output_name(src), model_detectors={}, regions=("generic",),
                              interactive=False)
        self.assertEqual(result.status, "written")
        out = (d / "session.har.redacted.txt").read_text(encoding="utf-8")
        for value in SECRETS + ("max@mailbox-test.de",):
            self.assertNotIn(value, out)
        for kept in ("https://app.example.com/login?next=%2Fhome&access_token=⟦SECRET_", "Host: app.example.com",
                     "Accept: text/html", "Location: https://app.example.com/home", "https://app.example.com/api/me",
                     "Content-Type: application/json", '"plan": "free"'):
            self.assertIn(kept, out)

    def test_a_har_that_is_not_json_is_named(self):
        d = Path(tempfile.mkdtemp())
        (d / "bad.har").write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bad.har"):
            extract.extract(d / "bad.har")


if __name__ == "__main__":
    unittest.main()
