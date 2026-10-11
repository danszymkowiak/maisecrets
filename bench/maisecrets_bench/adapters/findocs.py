"""Generated tax and financial documents (TASK-11.37): the shapes of the user's highest-risk content, which the public
datasets hold little of. Swiss salary certificates and tax returns in German and French, bank statements, MT940 and
CSV exports, a QR-bill, US W-2 and 1099 forms and an invoice, filled from a fixed seed.

Positives carry valid checksums: CH IBAN (mod 97), AHV/AVS 756 numbers (EAN-13), CHE UIDs (mod 11), card numbers
(Luhn), ABA routing numbers, US SSNs of a valid shape. Negatives look like them: amounts, dates, invoice, control and
personnel numbers, postal codes and QR references (mod 10 recursive). AHV, UID and EIN are labelled but out of scope
until the detector claims them (TASK-20 adds the Swiss types). Names are random syllables; no real value anywhere.

Unlike the synthetic tool output, this set is scored (user, 2026-10-11), with the caveat that it is tuned to our own
generator (docs/BENCHMARK.md)."""
from __future__ import annotations

import hashlib
import random
import string
from pathlib import Path
from typing import Callable, Iterator

from ..labels import LabelTable
from ..schema import Sample, Span
from ..split import split_of
from .synthetic import Doc, Gen

DATASET = "findocs"
SEED = 20261012
PER_TEMPLATE = 300
_QR_TABLE = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)


def version() -> str:
    """The seed, the size and this file: a change to a generator builds the dataset again."""
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    return f"seed{SEED}-n{PER_TEMPLATE}-{h}"


# checksums (test vectors in bench/tests/test_findocs.py)
def ean13_check(digits12: str) -> int:
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits12))
    return (10 - s % 10) % 10


def uid_check(digits8: str) -> int:
    """CHE UID: weights 5,4,3,2,7,6,5,4; 11 minus the remainder, 11 -> 0; 10 means no valid number."""
    s = sum(int(d) * w for d, w in zip(digits8, (5, 4, 3, 2, 7, 6, 5, 4)))
    return (11 - s % 11) % 11


def mod10_recursive(digits: str) -> int:
    carry = 0
    for d in digits:
        carry = _QR_TABLE[(carry + int(d)) % 10]
    return (10 - carry) % 10


def _iban_check(country: str, bban: str) -> str:
    num = "".join(str(int(c, 36)) for c in bban + country + "00")
    return f"{98 - int(num) % 97:02d}"


def _groups(s: str, n: int = 4) -> str:
    return " ".join(s[i:i + n] for i in range(0, len(s), n))


class FinGen(Gen):
    """Finance-shaped values from one seeded random source."""

    def digits(self, n: int) -> str:
        return self.s(string.digits, n)

    def iban_ch(self, qr: bool = False, spaced: bool = True) -> str:
        bank = str(self.r.randrange(30000, 32000)) if qr else f"{self.r.randrange(100, 9999):05d}"
        bban = bank + self.digits(12)
        iban = "CH" + _iban_check("CH", bban) + bban
        return _groups(iban) if spaced else iban

    def ahv(self) -> str:
        d = "756" + self.digits(9)
        d += str(ean13_check(d))
        return f"{d[:3]}.{d[3:7]}.{d[7:11]}.{d[11:]}"

    def uid(self) -> str:
        while True:
            d = self.digits(8)
            c = uid_check(d)
            if c != 10:
                d += str(c)
                return f"CHE-{d[:3]}.{d[3:6]}.{d[6:]}"

    def qr_ref(self) -> str:
        d = self.digits(26)
        d += str(mod10_recursive(d))
        return d[:2] + " " + _groups(d[2:], 5)

    def card(self) -> str:
        body = "4" + self.digits(14)
        total = 0
        for i, ch in enumerate(reversed(body)):
            n = int(ch) * (2 if i % 2 == 0 else 1)
            total += n - 9 if n > 9 else n
        return _groups(body + str((10 - total % 10) % 10))

    def ssn(self) -> str:
        area = self.r.choice([a for a in range(1, 900) if a != 666])
        return f"{area:03d}-{self.r.randrange(1, 100):02d}-{self.r.randrange(1, 10000):04d}"

    def ein(self) -> str:
        return f"{self.r.randrange(10, 99)}-{self.digits(7)}"

    def aba(self) -> str:
        d = self.digits(8)
        s = sum(int(x) * w for x, w in zip(d, (3, 7, 1, 3, 7, 1, 3, 7)))
        return d + str((10 - s % 10) % 10)

    def account_us(self) -> str:
        return self.digits(self.r.randrange(9, 13))

    def phone_ch(self) -> str:
        return f"+41 {self.r.choice([21, 22, 31, 44, 61, 71])} {self.digits(3)} {self.digits(2)} {self.digits(2)}"

    def phone_us(self) -> str:
        return f"({self.r.randrange(201, 990)}) {self.r.randrange(200, 999)}-{self.digits(4)}"

    def name(self) -> str:
        def word() -> str:
            return "".join(self.r.choice(["ba", "ke", "lo", "mi", "ra", "su", "ti", "no", "ve", "da"])
                           for _ in range(self.r.randrange(2, 4))).capitalize()
        return f"{word()} {word()}"

    def chf(self, lo: int = 100, hi: int = 150000) -> str:
        v = self.r.randrange(lo * 100, hi * 100)
        return f"{v // 100:,}".replace(",", "'") + f".{v % 100:02d}"

    def usd(self, lo: int = 100, hi: int = 150000) -> str:
        v = self.r.randrange(lo * 100, hi * 100)
        return f"{v // 100:,}.{v % 100:02d}"

    def date_ch(self) -> str:
        return f"{self.r.randrange(1, 29):02d}.{self.r.randrange(1, 13):02d}.{self.r.randrange(2023, 2026)}"

    def date_us(self) -> str:
        return f"{self.r.randrange(1, 13):02d}/{self.r.randrange(1, 29):02d}/{self.r.randrange(2023, 2026)}"

    def plz(self) -> str:
        return str(self.r.randrange(1000, 9700))


def t_lohnausweis_de(g: FinGen) -> Doc:
    d = Doc().add("Lohnausweis 2025 - Formular 11\nA  Arbeitgeber: ").add(g.name().split()[0] + " Treuhand AG, UID ")
    d.pos(g.uid(), "CHE_UID").add("\n   Bahnhofstrasse 12, ").neg(g.plz(), "POSTCODE").add(" Zürich\n")
    d.add(f"B  Arbeitnehmer: {g.name()}\n   AHV-Nr. ").pos(g.ahv(), "AHV").add("\n   Geburtsdatum ")
    d.neg(g.date_ch(), "DATE").add("\n   Personalnummer ").neg(g.digits(6), "REF").add("\n")
    for label in ("1. Lohn", "9. Beiträge AHV/IV/EO/ALV/NBUV", "10. Berufliche Vorsorge", "11. Nettolohn"):
        d.add(f"{label:<34} CHF ").neg(g.chf(), "AMOUNT").add("\n")
    d.add("Rückfragen: ").pos(g.email(), "EMAIL").add(", Tel. ").pos(g.phone_ch(), "PHONE").add("\n")
    return d


def t_certificat_fr(g: FinGen) -> Doc:
    d = Doc().add("Certificat de salaire 2025 - formulaire 11\nA  Employeur : ").add(g.name().split()[1] + " SA, IDE ")
    d.pos(g.uid(), "CHE_UID").add("\n   Rue du Rhône 8, ").neg(g.plz(), "POSTCODE").add(" Genève\n")
    d.add(f"B  Employé : {g.name()}\n   N° AVS ").pos(g.ahv(), "AHV").add("\n   Date de naissance ")
    d.neg(g.date_ch(), "DATE").add("\n   N° du personnel ").neg(g.digits(6), "REF").add("\n")
    for label in ("1. Salaire", "9. Cotisations AVS/AI/APG/AC/AANP", "10. Prévoyance professionnelle",
                  "11. Salaire net"):
        d.add(f"{label:<36} CHF ").neg(g.chf(), "AMOUNT").add("\n")
    d.add("Contact : ").pos(g.email(), "EMAIL").add(", tél. ").pos(g.phone_ch(), "PHONE").add("\n")
    return d


def t_steuererklaerung_de(g: FinGen) -> Doc:
    d = Doc().add("Steuererklärung 2025 - natürliche Personen\nGemeinde-Nr. ").neg(str(g.r.randrange(1, 300)), "REF")
    d.add(f"\nSteuerpflichtige Person: {g.name()}, AHV-Nr. ").pos(g.ahv(), "AHV")
    d.add("\nEinkommen aus unselbständiger Erwerbstätigkeit CHF ").neg(g.chf(), "AMOUNT")
    d.add("\nWertschriftenertrag CHF ").neg(g.chf(10, 5000), "AMOUNT")
    d.add("\nAbzug Säule 3a CHF ").neg(g.chf(1000, 7300), "AMOUNT")
    d.add("\nRückerstattung des Verrechnungssteuer-Guthabens auf das Konto IBAN ").pos(g.iban_ch(), "IBAN")
    d.add("\nEingereicht am ").neg(g.date_ch(), "DATE").add(", Rückfragen an ").pos(g.email(), "EMAIL").add("\n")
    return d


def t_releve_fr(g: FinGen) -> Doc:
    d = Doc().add(f"Relevé de compte\nTitulaire : {g.name()}\nIBAN ").pos(g.iban_ch(), "IBAN")
    d.add("\nPériode du ").neg(g.date_ch(), "DATE").add(" au ").neg(g.date_ch(), "DATE").add("\n\n")
    for _ in range(g.r.randrange(2, 5)):
        d.neg(g.date_ch(), "DATE").add(f"  Virement à {g.name()}, IBAN ").pos(g.iban_ch(), "IBAN")
        d.add("  CHF -").neg(g.chf(10, 9000), "AMOUNT").add("\n")
    d.neg(g.date_ch(), "DATE").add("  Paiement QR, référence ").neg(g.qr_ref(), "QR_REF").add("  CHF -")
    d.neg(g.chf(10, 2000), "AMOUNT").add("\nSolde final CHF ").neg(g.chf(), "AMOUNT").add("\n")
    return d


def t_kontoauszug_de(g: FinGen) -> Doc:
    d = Doc().add(f"Kontoauszug Privatkonto\nKontoinhaber: {g.name()}\nIBAN ").pos(g.iban_ch(), "IBAN")
    d.add("\nBuchungsdatum  Text  Betrag CHF\n")
    for _ in range(g.r.randrange(2, 5)):
        d.neg(g.date_ch(), "DATE").add(f"  Gutschrift {g.name()}  ").neg(g.chf(10, 9000), "AMOUNT").add("\n")
    d.neg(g.date_ch(), "DATE").add("  Zahlung QR-Rechnung, Referenz ").neg(g.qr_ref(), "QR_REF")
    d.add("  -").neg(g.chf(10, 3000), "AMOUNT").add("\nKarte ").pos(g.card(), "CARD").add(" Bezug Bancomat  -")
    d.neg(g.chf(20, 1000), "AMOUNT").add("\n")
    return d


def _mt940_amount(g: FinGen) -> str:
    return f"{g.r.randrange(1, 90000)},{g.r.randrange(100):02d}"


def t_mt940(g: FinGen) -> Doc:
    d = Doc().add(":20:STARTUMS\n:25:").pos(g.iban_ch(spaced=False), "IBAN").add("\n:28C:")
    d.neg(f"{g.r.randrange(1, 400):05d}/001", "REF").add("\n:60F:C251001CHF").neg(_mt940_amount(g), "AMOUNT")
    for _ in range(g.r.randrange(1, 4)):
        d.add("\n:61:2510").add(f"{g.r.randrange(1, 29):02d}").add("D").neg(_mt940_amount(g), "AMOUNT")
        d.add("NTRFNONREF//").neg(g.digits(10), "REF")
        d.add(f"\n:86:?20Zahlung Rechnung {g.r.randrange(2024, 2026)}-{g.r.randrange(1, 999):03d}?31")
        d.pos(g.iban_ch(spaced=False), "IBAN").add(f"?32{g.name().upper()}")
    d.add("\n:62F:C251031CHF").neg(_mt940_amount(g), "AMOUNT").add("\n-\n")
    return d


def t_bank_csv(g: FinGen) -> Doc:
    d = Doc().add("Datum;Buchungstext;Gegenkonto IBAN;Betrag;Saldo\n")
    for _ in range(g.r.randrange(3, 6)):
        d.neg(g.date_ch(), "DATE").add(f";Zahlung an {g.name()};").pos(g.iban_ch(spaced=False), "IBAN").add(";-")
        d.neg(g.chf(10, 9000).replace("'", ""), "AMOUNT").add(";").neg(g.chf().replace("'", ""), "AMOUNT").add("\n")
    return d


def t_w2(g: FinGen) -> Doc:
    d = Doc().add("Form W-2 Wage and Tax Statement 2025\na Employee's social security number  ").pos(g.ssn(), "SSN")
    d.add("\nb Employer identification number (EIN)  ").pos(g.ein(), "EIN")
    d.add(f"\nc Employer's name, address, and ZIP code  {g.name().split()[0]} Logistics Inc, 400 Market St, "
          f"San Francisco, CA ").neg(f"{g.r.randrange(10000, 99950)}", "POSTCODE")
    d.add("\nd Control number  ").neg(g.digits(8), "REF").add(f"\ne Employee's name  {g.name()}")
    for label in ("1 Wages, tips, other compensation", "2 Federal income tax withheld", "3 Social security wages",
                  "4 Social security tax withheld"):
        d.add(f"\n{label}  ").neg(g.usd(), "AMOUNT")
    return d.add("\n")


def t_1099(g: FinGen) -> Doc:
    d = Doc().add("Form 1099-INT Interest Income 2025\nPAYER'S TIN  ").pos(g.ein(), "EIN")
    d.add("\nRECIPIENT'S TIN  ").pos(g.ssn(), "SSN").add(f"\nRECIPIENT'S name  {g.name()}")
    d.add("\nAccount number (see instructions)  ").pos(g.account_us(), "ACCOUNT")
    d.add("\n1 Interest income  $").neg(g.usd(10, 20000), "AMOUNT")
    d.add("\n4 Federal income tax withheld  $").neg(g.usd(0, 3000), "AMOUNT")
    d.add("\nDirect deposit: routing number ").pos(g.aba(), "ABA").add(", account ").pos(g.account_us(), "ACCOUNT")
    d.add("\nQuestions: ").pos(g.email(), "EMAIL").add(" or ").pos(g.phone_us(), "PHONE").add("\n")
    return d


def t_invoice_en(g: FinGen) -> Doc:
    d = Doc().add("INVOICE  No. ").neg(f"INV-{g.r.randrange(2024, 2026)}-{g.digits(5)}", "REF").add("\nDate: ")
    d.neg(g.date_us(), "DATE").add(f"\nBill to: {g.name()}\n")
    for _ in range(g.r.randrange(2, 4)):
        d.add(f"  Consulting services, {g.r.randrange(1, 40)} h  $").neg(g.usd(100, 9000), "AMOUNT").add("\n")
    d.add("Total due: $").neg(g.usd(500, 30000), "AMOUNT").add("\nPaid by card ").pos(g.card(), "CARD")
    d.add("\nOr ACH to routing ").pos(g.aba(), "ABA").add(", account ").pos(g.account_us(), "ACCOUNT")
    d.add("\nBilling questions: ").pos(g.email(), "EMAIL").add(", ").pos(g.phone_us(), "PHONE").add("\n")
    return d


def t_qr_bill_fr(g: FinGen) -> Doc:
    d = Doc().add("Section paiement\nCompte / Payable à\n").pos(g.iban_ch(qr=True), "IBAN")
    d.add(f"\n{g.name()}\nRue de Lausanne 14\n").neg(g.plz(), "POSTCODE").add(" Lausanne\nRéférence\n")
    d.neg(g.qr_ref(), "QR_REF").add("\nInformations supplémentaires\nFacture ")
    d.neg(f"{g.r.randrange(2024, 2026)}-{g.digits(4)}", "REF").add(" du ").neg(g.date_ch(), "DATE")
    d.add("\nMonnaie  Montant\nCHF  ").neg(g.chf(10, 5000), "AMOUNT").add("\n")
    return d


# template -> (function, language of the bench's groups, locale tag)
TEMPLATES: dict[str, tuple[Callable[[FinGen], Doc], str, str]] = {
    "lohnausweis_de": (t_lohnausweis_de, "de", "de_CH"), "certificat_fr": (t_certificat_fr, "fr", "fr_CH"),
    "steuererklaerung_de": (t_steuererklaerung_de, "de", "de_CH"), "releve_fr": (t_releve_fr, "fr", "fr_CH"),
    "kontoauszug_de": (t_kontoauszug_de, "de", "de_CH"), "mt940": (t_mt940, "de", "de_CH"),
    "bank_csv": (t_bank_csv, "de", "de_CH"), "w2": (t_w2, "en", "en_US"), "f1099": (t_1099, "en", "en_US"),
    "invoice_en": (t_invoice_en, "en", "en_US"), "qr_bill_fr": (t_qr_bill_fr, "fr", "fr_CH"),
}


def samples(table: LabelTable, per_template: int = PER_TEMPLATE, seed: int = SEED) -> Iterator[Sample]:
    g = FinGen(random.Random(seed))
    for name, (template, language, locale) in TEMPLATES.items():
        for i in range(per_template):
            d = template(g)
            sid = f"{name}:{i}"
            spans = [Span(a, b, label, table.type_of(label), gold) for a, b, label, gold in d.spans]
            yield Sample(DATASET, sid, sid, language, d.text, spans, split_of(DATASET, sid),
                         [f"locale:{locale}", f"template:{name}"])
