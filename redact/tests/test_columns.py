"""A table's headers say what its cells hold (TASK-50). A browser password export (Firefox's logins.csv) came out with
its passwords in the clear: no rule fires on a bare value, and no model is asked for passwords. In the same file the
models took the record GUID for a national ID and the millisecond timestamps for account numbers (measured
2026-10-14: openai/privacy-filter and gliner2 label uppercase GUIDs ACCOUNT, pieces of them too)."""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact.adapters import compose as app  # noqa: E402

from maisecrets_redact.adapters import extract  # noqa: E402

from maisecrets_redact.domain import fields  # noqa: E402
from maisecrets_redact.domain.document import Document, Position, Span  # noqa: E402

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
            self.assertEqual(fields.header_type(h), "SECRET", h)

    def test_username_headers(self):
        for h in ("username", "user_name", "User", "login", "userId"):
            self.assertEqual(fields.header_type(h), "USERNAME", h)

    def test_other_headers_say_nothing(self):
        for h in ("url", "httpRealm", "formActionOrigin", "guid", "timePasswordChanged", "passwordHint", "token_type",
                  "secretary", "", "C"):
            self.assertIsNone(fields.header_type(h), h)


class HeaderWordTests(unittest.TestCase):
    """Headers match by their words, not by the end of the squashed name (code review 2026-10-14, TASK-56): Bitwarden's
    login_username was missed, an NLP table's token column and an isSecret flag were wiped, and a phone under candidate
    was taken for a timestamp."""

    def test_a_username_after_another_word(self):
        for h in ("login_username", "db_user", "email_username", "account_login", "Login Name", "userID"):
            self.assertEqual(fields.header_type(h), "USERNAME", h)

    def test_a_token_or_a_flag_is_not_a_secret_and_a_named_token_is(self):
        for h in ("token", "token_count", "isSecret", "has_password", "secretary", "last_login", "user_agent"):
            self.assertIsNone(fields.header_type(h), h)
        for h in ("access_token", "client_secret", "api_token", "accessToken", "refresh-token", "login_password"):
            self.assertEqual(fields.header_type(h), "SECRET", h)

    def test_time_headers_by_their_words(self):
        for h in ("candidate", "mandate", "lifetime", "validate", "phone"):
            self.assertFalse(fields._time_header(h), h)
        for h in ("timeCreated", "created_at", "createdAt", "date", "Date", "last_modified", "timeLastUsed",
                  "timestamp", "Last Modified"):
            self.assertTrue(fields._time_header(h), h)


class PersonalHeaderTests(unittest.TestCase):
    """A header that names a personal type makes its column a deterministic hit (TASK-51, user 2026-10-14: last_name
    should redact): the vote no longer decides a column the file already labels."""

    def test_personal_headers(self):
        cases = {"NAME": ("first_name", "lastName", "Last Name", "full_name", "surname", "given_name", "family_name",
                          "Vorname", "Nachname", "customer_name", "patient_name"),
                 "DOB": ("dob", "DOB", "date_of_birth", "birthdate", "birth_date", "Birthday", "Geburtsdatum"),
                 "NATIONAL_ID": ("ssn", "SSN", "social_security_number", "national_id", "ahv", "AHV-Nr"),
                 "PASSPORT": ("passport", "passport_number"),
                 "TAX_ID": ("tax_id", "TIN", "Steuernummer"),
                 "ACCOUNT": ("iban", "IBAN", "account_number", "accountNo", "bank_account", "Kontonummer"),
                 "PHONE": ("phone", "Phone Number", "mobile", "telephone", "tel", "fax", "home_phone", "Telefon"),
                 "ADDRESS": ("address", "street", "street_address", "address_line_1", "Address2", "billing_address",
                             "Strasse", "Adresse")}
        for typ, headers in cases.items():
            for h in headers:
                self.assertEqual(fields.header_type(h), typ, h)

    def test_a_2fa_seed_is_a_secret_and_notes_go_to_the_models(self):
        for h in ("totp", "TOTP", "login_totp", "OTPAuth", "otp", "mfa_secret"):
            self.assertEqual(fields.header_type(h), "SECRET", h)
        for h in ("notes", "Notes", "note", "extra", "Comments"):
            self.assertIsNone(fields.header_type(h), h)

    def test_no_hit_on_headers_that_only_look_personal(self):
        for h in ("name", "Name", "product_name", "city", "city_name", "company_name", "file_name", "Title", "account",
                  "Account", "email_address", "ip_address", "mac_address", "web_address", "phone_type", "is_mobile",
                  "birth_place", "zip", "country", "status", "grouping", "fav", "tags", "address_type"):
            self.assertIsNone(fields.header_type(h), h)


# Header rows of the CSV exports of six password managers (their documented formats), with one synthetic entry each:
# username testuser, password testpass-<k>, and a 2FA seed testseed-<k> where the format has a column for it.
EXPORTS = {
    "bitwarden": ("folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp",
                  ",,login,Example,a note,,0,https://example.com,testuser,testpass-bw,testseed-bw"),
    "chrome": ("name,url,username,password,note", "example.com,https://example.com,testuser,testpass-ch,a note"),
    "1password": ("Title,Url,Username,Password,OTPAuth,Favorite,Archived,Tags,Notes",
                  "Example,https://example.com,testuser,testpass-op,testseed-op,false,false,,a note"),
    "lastpass": ("url,username,password,totp,extra,name,grouping,fav",
                 "https://example.com,testuser,testpass-lp,testseed-lp,a note,Example,,0"),
    "keepass": ("Account,Login Name,Password,Web Site,Comments",
                "Example,testuser,testpass-kp,https://example.com,a note"),
    "keepassxc": ("Group,Title,Username,Password,URL,Notes,TOTP,Icon,Last Modified,Created",
                  "Root,Example,testuser,testpass-kx,https://example.com,a note,testseed-kx,0,"
                  "2026-01-01T00:00:00Z,2026-01-01T00:00:00Z"),
}


class PasswordManagerExportTests(unittest.TestCase):
    def test_every_username_password_and_2fa_seed_is_found_and_nothing_else(self):
        for name, (header, row) in EXPORTS.items():
            with self.subTest(export=name):
                path = Path(tempfile.mkdtemp()) / f"{name}.csv"
                path.write_text(header + "\n" + row + "\n", encoding="utf-8")
                doc = extract.extract(path)
                got = sorted((doc.text[s.start:s.end], s.type) for s in fields.column_spans(doc))
                k = row.split("testpass-")[1][:2]
                want = [(f"testpass-{k}", "SECRET"), ("testuser", "USERNAME")]
                if "testseed-" in row:
                    want.insert(1, (f"testseed-{k}", "SECRET"))
                self.assertEqual(got, want)


class ColumnSpanTests(unittest.TestCase):
    def test_the_password_and_username_cells_of_a_firefox_export(self):
        doc = firefox_export()
        got = [(doc.text[s.start:s.end], s.type) for s in fields.column_spans(doc)]
        self.assertEqual(got, [("testuser", "USERNAME"), ("testpass-fair", "SECRET")])

    def test_a_sheet_of_a_workbook(self):
        text = "[Logins]\npassword\tnote\ntestpass\tfine\n"
        i, j = text.index("password"), text.index("testpass")
        doc = Document("t.xlsx", text, (Position(i, i + 8, "sheet Logins, row 1, column password"),
                                        Position(j, j + 8, "sheet Logins, row 2, column password"),
                                        Position(j + 9, j + 13, "sheet Logins, row 2, column note")))
        self.assertEqual([(text[s.start:s.end], s.type) for s in fields.column_spans(doc)], [("testpass", "SECRET")])

    def test_a_text_file_has_no_columns(self):
        text = "password\ntestpass\n"
        self.assertEqual(fields.column_spans(Document("t.txt", text, (Position(0, len(text), "file"),))), [])


class IdShapeTests(unittest.TestCase):
    def test_a_model_span_on_a_guid_or_a_piece_of_one_is_dropped(self):
        doc = firefox_export()
        i = doc.text.index(GUID)
        spans = [at(doc, GUID, "NATIONAL_ID"), Span(i + 1, i + 9, "ACCOUNT", "m"), Span(i + 15, i + 19, "ACCOUNT", "m")]
        self.assertEqual(fields.plausible(doc, spans), [])

    def test_a_guid_under_an_id_header_is_dropped_whatever_its_label(self):
        # code review 2026-10-14, TASK-57: the drop holds where the column says the value is an id
        for header in ("guid", "uuid", "id", "ID", "customer_id", "recordUuid"):
            text = f"{header}\tnote\n{GUID}\tx\n"
            n = text.index(GUID)
            d = Document("t.csv", text, (Position(0, len(header), f"row 1, column {header}"),
                                         Position(n, n + len(GUID), f"row 2, column {header}")))
            for typ in ("SECRET", "ACCOUNT", "NATIONAL_ID"):
                self.assertEqual(fields.plausible(d, [Span(n, n + len(GUID), typ, "m")]), [], (header, typ))

    def test_a_guid_elsewhere_labelled_a_secret_goes_to_review(self):
        # a UUID-shaped API key or customer id: dropped, it was written in the clear; redacted, every record id goes
        key = GUID[1:-1].upper()
        plain = Document("t.txt", f"the deploy key is {key} for prod")
        for typ in ("SECRET", "ACCOUNT"):
            span = at(plain, key, typ)
            self.assertEqual(fields.plausible(plain, [span]), [span], typ)
            self.assertEqual(fields.doubtful(plain, [span]), [span], typ)
        text = f"note\n{key}\n"
        n = text.index(key)
        cell = Document("t.csv", text, (Position(0, 4, "row 1, column note"),
                                        Position(n, n + len(key), "row 2, column note")))
        self.assertEqual(fields.plausible(cell, [Span(n, n + len(key), "ACCOUNT", "m")]), [],
                         "models label a bare GUID in a table an account")
        secret = Span(n, n + len(key), "SECRET", "m")
        self.assertEqual((fields.plausible(cell, [secret]), fields.doubtful(cell, [secret])), ([secret], [secret]))
        self.assertEqual(fields.doubtful(plain, [at(plain, "prod", "NAME")]), [])

    def test_two_models_on_a_doubtful_guid_ask_instead_of_redacting(self):
        from maisecrets_redact.domain import vote
        key = GUID[1:-1].upper()
        doc = Document("t.txt", f"the deploy key is {key} for prod")
        spans = {"a": [at(doc, key, "SECRET", "a")], "b": [at(doc, key, "SECRET", "b")]}
        d = vote.decide(doc, [], spans, k=2, ask=[s for v in spans.values() for s in fields.doubtful(doc, v)])
        self.assertEqual((d.redact, [doc.text[s.start:s.end] for s in d.review]), ((), [key]))

    def test_a_timestamp_under_a_time_header_is_dropped_and_the_same_number_elsewhere_stays(self):
        doc = firefox_export()
        stamps = [at(doc, n, "ACCOUNT") for n in ("1710000000001", "1720000000002", "1730000000003")]
        self.assertEqual(fields.plausible(doc, stamps), [])
        for header in ("created_at", "createdAt", "Date", "modified"):
            text = f"{header}\n1710000000001\n"
            n = text.index("171")
            d = Document("t.csv", text, (Position(0, len(header), f"row 1, column {header}"),
                                         Position(n, n + 13, f"row 2, column {header}")))
            self.assertEqual(fields.plausible(d, [Span(n, n + 13, "ACCOUNT", "m")]), [], header)
        text = "account\n1710000000001\n"
        d = Document("t.csv", text, (Position(0, 7, "row 1, column account"), Position(8, 21, "row 2, column account")))
        self.assertEqual(len(fields.plausible(d, [Span(8, 21, "ACCOUNT", "m")])), 1)


class FirefoxExportTests(unittest.TestCase):
    """The whole file through run_file, with two fake models that answer as the real ones did."""

    def test_passwords_and_usernames_go_urls_guids_and_timestamps_stay(self):
        d = Path(tempfile.mkdtemp())
        src, out = d / "logins.csv", d / "logins.csv.redacted.csv"
        src.write_text(HEADER + "\n" + ROW + "\n", encoding="utf-8")

        def model(name):
            def find(doc):
                return [at(doc, GUID, "NATIONAL_ID", name)] + [at(doc, n, "ACCOUNT", name) for n in
                                                               ("1710000000001", "1720000000002", "1730000000003")]
            return find
        result = app.run_file(src, out, model_detectors={"m1": model("m1"), "m2": model("m2")}, regions=("generic",),
                              interactive=False)
        self.assertEqual(result.status, "written")
        header, row = csv.reader(io.StringIO(out.read_text(encoding="utf-8"), newline=""))
        self.assertEqual(header, HEADER.split(","))
        self.assertEqual(row, ["https://login.example.com", "⟦USERNAME_1⟧", "⟦SECRET_1⟧", "",
                                           "https://sso.example.com", GUID, "1710000000001", "1720000000002",
                                           "1730000000003"])
