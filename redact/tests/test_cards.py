"""vCard and iCalendar exports (TASK-53): a contact list (.vcf) and a calendar (.ics) label each line, so a labelled
line is a deterministic hit of its type (FN a NAME, TEL a PHONE, ATTENDEE an EMAIL, its CN a NAME); free text (NOTE,
SUMMARY, DESCRIPTION) goes to the rules and models, and a meeting passcode in it is a SECRET. Folded lines (RFC 6350,
RFC 5545) are unfolded first. All values are synthetic.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact.adapters import compose as app  # noqa: E402

from maisecrets_redact.adapters import extract  # noqa: E402

from maisecrets_redact.domain import fields  # noqa: E402

VCF = ("BEGIN:VCARD\r\nVERSION:4.0\r\nFN:Erika Musterfrau\r\nN:Musterfrau;Erika;;;\r\n"
       "TEL;TYPE=cell:+41 79 000 00 01\r\nEMAIL;TYPE=home:erika@mailbox-test.de\r\n"
       "ADR;TYPE=home:;;Bahnhofstr\r\n asse 12;Zuerich;;8001;Schweiz\r\nBDAY:19870314\r\n"
       "item1.TEL:+41 44 000 00 02\r\nORG:Example AG\r\nNOTE:met at the fair\r\n"
       "PHOTO;ENCODING=b;TYPE=JPEG:iVBORw0KGgoAAAANSUhEUg\r\nEND:VCARD\r\n"
       "BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Max Muster\r\nTEL:+49 30 0000000\r\nEND:VCARD\r\n")

URL_PWD = "testpwd" + "-url"          # built here: the tree's own secret scan reads every literal
ICS = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\nBEGIN:VEVENT\r\nUID:abc-123@example.com\r\n"
       "DTSTART:20261020T090000Z\r\nSUMMARY:Quarterly review\r\n"
       "ORGANIZER;CN=Erika Musterfrau:mailto:erika@mailbox-test.de\r\n"
       "ATTENDEE;CN=\"Muster, Max\";ROLE=REQ-PARTICIPANT:mailto:max@mailbox-test.de\r\n"
       "LOCATION:Bahnhofstrasse 12, Zuerich\r\n"
       f"DESCRIPTION:Join https://meet.example.com/j/123?pwd={URL_PWD}\\nPasscode: 48\r\n 2910\r\n"
       "END:VEVENT\r\nEND:VCALENDAR\r\n")


def write(name: str, text: str) -> Path:
    path = Path(tempfile.mkdtemp()) / name
    path.write_bytes(text.encode("utf-8"))
    return path


def hits(doc) -> dict[str, str]:
    return {doc.text[s.start:s.end]: s.type for s in fields.card_spans(doc)}


class VcardTests(unittest.TestCase):
    def test_folded_lines_are_unfolded_and_fields_are_positions(self):
        doc = extract.extract(write("contacts.vcf", VCF))
        self.assertIn(";;Bahnhofstrasse 12;Zuerich;;8001;Schweiz", doc.text)
        i = doc.text.index("+41 79")
        self.assertEqual([p.where for p in doc.positions if p.start <= i < p.end], ["card 1, field TEL"])
        self.assertNotIn("iVBORw0KGgo", doc.text, "a photo is left out")

    def test_every_name_phone_email_address_and_birthday_is_a_hit(self):
        got = hits(extract.extract(write("contacts.vcf", VCF)))
        self.assertEqual(got, {"Erika Musterfrau": "NAME", "Musterfrau;Erika;;;": "NAME", "+41 79 000 00 01": "PHONE",
                               "erika@mailbox-test.de": "EMAIL", ";;Bahnhofstrasse 12;Zuerich;;8001;Schweiz": "ADDRESS",
                               "19870314": "DOB", "+41 44 000 00 02": "PHONE", "Max Muster": "NAME",
                               "+49 30 0000000": "PHONE"})

    def test_the_output_keeps_the_labels_and_the_free_text(self):
        src = write("contacts.vcf", VCF)
        self.assertEqual(app.run_file(src, src.with_name(app.output_name(src)), model_detectors={},
                                      regions=("generic",), interactive=False).status, "written")
        out = src.with_name("contacts.vcf.redacted.txt").read_text(encoding="utf-8")
        for value in ("Erika", "Musterfrau", "+41 79", "erika@", "Bahnhofstr", "19870314", "Max Muster", "+49 30"):
            self.assertNotIn(value, out)
        for kept in ("FN:", "TEL;TYPE=cell:", "ORG:Example AG", "NOTE:met at the fair"):
            self.assertIn(kept, out)


class IcalendarTests(unittest.TestCase):
    def test_organizer_attendees_their_names_and_location_are_hits(self):
        got = hits(extract.extract(write("cal.ics", ICS)))
        self.assertEqual(got["mailto:erika@mailbox-test.de"], "EMAIL")
        self.assertEqual(got["Erika Musterfrau"], "NAME")
        self.assertEqual(got['"Muster, Max"'], "NAME")
        self.assertEqual(got["mailto:max@mailbox-test.de"], "EMAIL")
        self.assertEqual(got["Bahnhofstrasse 12, Zuerich"], "ADDRESS")
        self.assertEqual(got["testpwd-url"], "SECRET")
        self.assertEqual(got["482910"], "SECRET")
        self.assertNotIn("Quarterly review", got)

    def test_the_output_has_no_person_place_or_passcode(self):
        src = write("cal.ics", ICS)
        app.run_file(src, src.with_name(app.output_name(src)), model_detectors={}, regions=("generic",),
                     interactive=False)
        out = src.with_name("cal.ics.redacted.txt").read_text(encoding="utf-8")
        for value in ("Erika", "Muster", "mailbox-test", "Bahnhofstrasse", "testpwd-url", "482910"):
            self.assertNotIn(value, out)
        # the plugin's URL rule takes pwd= up to the next blank, here with the escaped \nPasscode: label after it
        for kept in ("SUMMARY:Quarterly review", "ROLE=REQ-PARTICIPANT", "https://meet.example.com/j/123?pwd=",
                     "DTSTART:20261020T090000Z"):
            self.assertIn(kept, out)

    def test_positions_name_the_event_and_the_field(self):
        doc = extract.extract(write("cal.ics", ICS))
        i = doc.text.index('"Muster, Max"')
        self.assertEqual([p.where for p in doc.positions if p.start <= i < p.end], ["event 1, field ATTENDEE CN"])


if __name__ == "__main__":
    unittest.main()
