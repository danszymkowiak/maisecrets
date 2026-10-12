"""A card number needs a context word nearby (Presidio scores the bare shape 0.3), and the vendored words were English
only: 'Karte 4076 ...' in a German bank statement was missed (TASK-24, findocs). The card words of the label
languages count too; the number must still pass Luhn.

Run: python3 -m unittest tests.test_card_context -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import detect  # noqa: E402

CARD = "4111 1111 1111 1111"            # the common Luhn test number
BAD = "4111 1111 1111 1112"


def cards(text: str) -> list[str]:
    return [m.value for m in detect.scan(text) if m.type == "CARD"]


class CardContextTests(unittest.TestCase):
    def test_a_card_word_in_another_language_counts(self):
        for text in (f"Karte {CARD} Bezug Bancomat", f"Kreditkarte: {CARD}", f"Kartennummer {CARD}",
                     f"Debitkarte {CARD}", f"numéro de carte {CARD}", f"carte bancaire {CARD}",
                     f"carta di credito {CARD}", f"número de tarjeta {CARD}", f"creditcard {CARD}"):
            with self.subTest(text=text):
                self.assertEqual(cards(text), [CARD])

    def test_luhn_still_decides(self):
        self.assertEqual(cards(f"Karte {BAD} Bezug Bancomat"), [])

    def test_without_a_card_word_the_bare_number_stays_unreported(self):
        self.assertEqual(cards(f"Referenz {CARD} vom Konto"), [])
        self.assertEqual(cards(f"Kartoffel {CARD}"), [], "a whole word only: Kartoffel is no Karte")


if __name__ == "__main__":
    unittest.main()
