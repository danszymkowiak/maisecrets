"""A table's headers say what its cells hold (TASK-50). A browser password export (Firefox's logins.csv) came out with
its passwords in the clear: no rule fires on a bare value, and no model is asked for passwords. In the same file the
models took the record GUID for a national ID and the millisecond timestamps for account numbers (measured
2026-10-14: openai/privacy-filter and gliner2 label uppercase GUIDs ACCOUNT, pieces of them too)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact import app, extract, pipeline  # noqa: E402
from maisecrets_redact.pipeline import Document, Position, Span  # noqa: E402

HEADER = "url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged"
GUID = "{3c05ac01-0000-4000-8000-00000000c0de}"
ROW = f"https://login.example.com,testuser,testpass-fair,,https://sso.example.com,{GUID},1710000000001,1720000000002,1730000000003"


def firefox_export() -> Document:
    path = Path(tempfile.mkdtemp()) / "logins.csv"
    path.write_text(HEADER + "\n" + ROW + "\n", encoding="utf-8")
    return extract.extract(path)


def at(doc: Document, value: str, typ: str, source: str = "m") -> Span:
    i = doc.text.index(value)
    return Span(i, i + len(value), typ, source)


class HeaderTests(unittest.TestCase):
    def test_secret_headers(self):
        for h in ("password", "Password", "db_password", "passwd", "pwd", "Passphrase", "client_secret", "api-key",
                  "apiKey", "access_token", "private key"):
            self.assertEqual(pipeline.header_type(h), "SECRET", h)

    def test_username_headers(self):
        for h in ("username", "user_name", "User", "login", "userId"):
            self.assertEqual(pipeline.header_type(h), "USERNAME", h)

    def test_other_headers_say_nothing(self):
        for h in ("url", "httpRealm", "formActionOrigin", "guid", "timePasswordChanged", "passwordHint", "token_type",
                  "secretary", "", "C"):
            self.assertIsNone(pipeline.header_type(h), h)


class ColumnSpanTests(unittest.TestCase):
    def test_the_password_and_username_cells_of_a_firefox_export(self):
        doc = firefox_export()
        got = [(doc.text[s.start:s.end], s.type) for s in pipeline.column_spans(doc)]
        self.assertEqual(got, [("testuser", "USERNAME"), ("testpass-fair", "SECRET")])

    def test_a_sheet_of_a_workbook(self):
        text = "[Logins]\npassword\tnote\ntestpass\tfine\n"
        i, j = text.index("password"), text.index("testpass")
        doc = Document("t.xlsx", text, (Position(i, i + 8, "sheet Logins, row 1, column password"),
                                        Position(j, j + 8, "sheet Logins, row 2, column password"),
                                        Position(j + 9, j + 13, "sheet Logins, row 2, column note")))
        self.assertEqual([(text[s.start:s.end], s.type) for s in pipeline.column_spans(doc)], [("testpass", "SECRET")])

    def test_a_text_file_has_no_columns(self):
        text = "password\ntestpass\n"
        self.assertEqual(pipeline.column_spans(Document("t.txt", text, (Position(0, len(text), "file"),))), [])


class IdShapeTests(unittest.TestCase):
    def test_a_model_span_on_a_guid_or_a_piece_of_one_is_dropped(self):
        doc = firefox_export()
        i = doc.text.index(GUID)
        spans = [at(doc, GUID, "NATIONAL_ID"), Span(i + 1, i + 9, "ACCOUNT", "m"), Span(i + 15, i + 19, "ACCOUNT", "m")]
        self.assertEqual(pipeline.plausible(doc, spans), [])
        text = f"record {GUID[1:-1].upper()} of Max"
        plain = Document("t.txt", text)
        self.assertEqual(pipeline.plausible(plain, [at(plain, GUID[1:-1].upper(), "ACCOUNT")]), [])

    def test_a_timestamp_under_a_time_header_is_dropped_and_the_same_number_elsewhere_stays(self):
        doc = firefox_export()
        stamps = [at(doc, n, "ACCOUNT") for n in ("1710000000001", "1720000000002", "1730000000003")]
        self.assertEqual(pipeline.plausible(doc, stamps), [])
        for header in ("created_at", "createdAt", "Date", "modified"):
            text = f"{header}\n1710000000001\n"
            n = text.index("171")
            d = Document("t.csv", text, (Position(0, len(header), f"row 1, column {header}"),
                                         Position(n, n + 13, f"row 2, column {header}")))
            self.assertEqual(pipeline.plausible(d, [Span(n, n + 13, "ACCOUNT", "m")]), [], header)
        text = "account\n1710000000001\n"
        d = Document("t.csv", text, (Position(0, 7, "row 1, column account"), Position(8, 21, "row 2, column account")))
        self.assertEqual(len(pipeline.plausible(d, [Span(8, 21, "ACCOUNT", "m")])), 1)


class FirefoxExportTests(unittest.TestCase):
    """The whole file through run_file, with two fake models that answer as the real ones did."""

    def test_passwords_and_usernames_go_urls_guids_and_timestamps_stay(self):
        d = Path(tempfile.mkdtemp())
        src, out = d / "logins.csv", d / "logins.csv.redacted.txt"
        src.write_text(HEADER + "\n" + ROW + "\n", encoding="utf-8")

        def model(name):
            def find(doc):
                return [at(doc, GUID, "NATIONAL_ID", name)] + [at(doc, n, "ACCOUNT", name) for n in
                                                               ("1710000000001", "1720000000002", "1730000000003")]
            return find
        result = app.run_file(src, out, model_detectors={"m1": model("m1"), "m2": model("m2")}, regions=("generic",),
                              interactive=False)
        self.assertEqual(result.status, "written")
        header, row = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(header.split("\t"), HEADER.split(","))
        self.assertEqual(row.split("\t"), ["https://login.example.com", "⟦USERNAME_1⟧", "⟦SECRET_1⟧", "",
                                           "https://sso.example.com", GUID, "1710000000001", "1720000000002",
                                           "1730000000003"])
