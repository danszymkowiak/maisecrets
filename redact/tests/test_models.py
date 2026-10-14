"""Local PII models behind one interface (TASK-34.4): long texts are chunked with overlap so a span across a chunk
boundary is still found once, model labels map to the tool's types, every model's licence is recorded, and only
permissive ones are defaults. A fake backend stands in for the real libraries (they are an optional extra).

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import unittest

from maisecrets_redact import models
from maisecrets_redact.pipeline import Document


class FakeBackend:
    """Finds the given words wherever they lie fully inside the chunk it is shown, as a model would."""

    def __init__(self, words: dict[str, str], seen: list | None = None):
        self.words, self.seen = words, seen if seen is not None else []

    def spans(self, text: str):
        self.seen.append(len(text))
        out = []
        for word, label in self.words.items():
            at = text.find(word)
            while at >= 0:
                out.append((at, at + len(word), label, 0.9))
                at = text.find(word, at + 1)
        return out


class ChunkTests(unittest.TestCase):
    def test_a_span_across_a_chunk_boundary_is_found_once(self):
        text = "x" * 990 + " Max Mustermann " + "y" * 990
        det = models.detector_from(FakeBackend({"Max Mustermann": "person"}), "fake", chunk=1000, overlap=100)
        spans = det(Document("t.txt", text))
        self.assertEqual([(s.start, s.end, s.type) for s in spans], [(991, 1005, "NAME")])

    def test_chunks_cover_the_text_and_stay_small(self):
        seen: list = []
        det = models.detector_from(FakeBackend({}, seen), "fake", chunk=1000, overlap=100)
        det(Document("t.txt", "z" * 5000))
        self.assertTrue(all(n <= 1000 for n in seen))
        self.assertGreaterEqual(sum(seen), 5000)

    def test_labels_map_to_the_tool_types_and_unknown_labels_are_dropped(self):
        det = models.detector_from(FakeBackend({"Max": "person", "Bahnhofstr. 1": "street address",
                                                "Acme": "organization"}), "fake")
        self.assertEqual(sorted(s.type for s in det(Document("t.txt", "Max, Bahnhofstr. 1, Acme"))),
                         ["ADDRESS", "NAME"])

    def test_spans_name_their_model_and_score(self):
        det = models.detector_from(FakeBackend({"Max": "person"}), "fake-model")
        (s,) = det(Document("t.txt", "Max"))
        self.assertEqual((s.source, s.score), ("fake-model", 0.9))


class WordCapTests(unittest.TestCase):
    """GLiNER drops every word after its 384th ("Sentence of length 387 has been truncated to 384", user report
    2026-10-14 on a CSV): a 2,000-character chunk of short cells holds more words than that, and the model never saw
    the end of it. A backend with `max_words` gets chunks of at most that many words, as GLiNER counts them."""

    def test_no_chunk_holds_more_words_than_the_backend_takes_and_the_end_is_still_seen(self):
        words: list = []

        class Capped(FakeBackend):
            max_words = 10

            def spans(self, text):
                words.append(len(models.WORD_RE.findall(text)))
                return super().spans(text)
        text = ",".join(f"r{i};{i}" for i in range(60)) + ",Max Mustermann"
        det = models.detector_from(Capped({"Max Mustermann": "person"}), "fake", chunk=2000, overlap=200)
        spans = det(Document("t.csv", text))
        self.assertTrue(words and max(words) <= 10, words)
        self.assertEqual([(text[s.start:s.end], s.type) for s in spans], [("Max Mustermann", "NAME")])

    def test_a_name_across_a_word_window_boundary_is_found_once(self):
        class Capped(FakeBackend):
            max_words = 12
        text = " ".join(["w"] * 11) + " Max Mustermann " + " ".join(["v"] * 11)
        det = models.detector_from(Capped({"Max Mustermann": "person"}), "fake")
        self.assertEqual(len(det(Document("t.txt", text))), 1)

    def test_the_gliner_backends_declare_their_cap(self):
        self.assertLess(models.GlinerBackend.max_words, 384)
        self.assertLess(models.Gliner2Backend.max_words, 384)


class QuietOfflineTests(unittest.TestCase):
    """A run with the models cached contacts no server (HF_HUB_OFFLINE: the tool keeps text private, and asked the
    Hub on every run, user report 2026-10-14), and the libraries' progress bars and advisories stay quiet."""

    def cache(self, *model_ids):
        import tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        for mid in model_ids:
            (root / "hub" / ("models--" + mid.replace("/", "--")) / "snapshots" / "abc").mkdir(parents=True)
        return {"HF_HOME": str(root)}

    def test_offline_only_when_every_model_is_cached(self):
        env = self.cache("a/one", "b/two")
        self.assertEqual(models.library_env(["a/one", "b/two"], env)["HF_HUB_OFFLINE"], "1")
        self.assertNotIn("HF_HUB_OFFLINE", models.library_env(["a/one", "c/three"], env))

    def test_the_libraries_are_quiet_and_a_setting_of_the_person_wins(self):
        env = self.cache()
        got = models.library_env(["a/one"], env)
        self.assertEqual(got["HF_HUB_DISABLE_PROGRESS_BARS"], "1")
        self.assertEqual(got["TRANSFORMERS_VERBOSITY"], "error")
        mine = models.library_env(["a/one"], {**env, "TRANSFORMERS_VERBOSITY": "info"})
        self.assertNotIn("TRANSFORMERS_VERBOSITY", mine)
        online = models.library_env(["a/one"], {**self.cache("a/one"), "HF_HUB_OFFLINE": "0"})
        self.assertNotIn("HF_HUB_OFFLINE", online)


class MergePiecesTests(unittest.TestCase):
    """openai/privacy-filter answers in word pieces with a leading space (measured 2026-10-12, TASK-34.8):
    ' Erika Muster' and 'frau' for one name."""

    def test_touching_pieces_of_one_label_become_one_span_without_edge_spaces(self):
        text = "an Erika Musterfrau, Tel. +41 44 555 01 23."
        pieces = [(2, 15, "private_person", 1.0), (15, 19, "private_person", 0.9),
                  (25, 40, "private_phone", 1.0), (40, 42, "private_phone", 0.8)]
        got = models.merge_pieces(text, pieces)
        self.assertEqual([(text[a:b], label, s) for a, b, label, s in got],
                         [("Erika Musterfrau", "private_person", 0.9), ("+41 44 555 01 23", "private_phone", 0.8)])

    def test_pieces_apart_or_of_another_label_or_on_another_line_stay_apart(self):
        text = "Erika, Max Muster\nBern"
        pieces = [(0, 5, "private_person", 1.0), (7, 10, "private_person", 1.0),
                  (10, 17, "private_address", 1.0), (17, 22, "private_address", 1.0)]
        got = models.merge_pieces(text, pieces)
        self.assertEqual([text[a:b] for a, b, _, _ in got], ["Erika", "Max", "Muster", "Bern"])


class PrivacyFilterLabelTests(unittest.TestCase):
    """openai/privacy-filter's labels (its config, 2026-10-12): account_number, private_address, private_date,
    private_email, private_person, private_phone, private_url, secret. private_date was not mapped, so every date it
    found was dropped and the bench showed 0 % of birth dates for it (TASK-34.8)."""

    def test_its_date_label_maps_to_the_birth_date_type(self):
        det = models.detector_from(FakeBackend({"14.03.1987": "private_date"}), "fake")
        self.assertEqual([s.type for s in det(Document("t.txt", "Geburtsdatum 14.03.1987"))], ["DOB"])

    def test_every_personal_label_it_emits_maps_to_a_type(self):
        for label in ("account_number", "private_address", "private_date", "private_email", "private_person",
                      "private_phone"):
            self.assertIn(label, models.LABELS, label)


class Gliner2Tests(unittest.TestCase):
    """gliner2's extract_entities with spans and confidence (fastino/gliner2-privacy-filter-PII-multi, gliner2 2.1.0,
    measured 2026-10-12): {"entities": {label: [{"text", "confidence", "start", "end"}]}}."""

    def test_the_answer_becomes_spans_and_its_labels_map_to_the_tool_types(self):
        result = {"entities": {"full_name": [{"text": "Erika Musterfrau", "confidence": 0.95, "start": 12, "end": 28}],
                               "street_address": [{"text": "Hauptstrasse 12", "confidence": 0.99, "start": 30,
                                                   "end": 45}],
                               "iban": [],
                               "phone_number": [{"text": "+41", "confidence": 0.9, "start": 66, "end": 69}]}}
        spans = models.gliner2_spans(result)
        self.assertEqual(sorted(spans), [(12, 28, "full_name", 0.95), (30, 45, "street_address", 0.99),
                                         (66, 69, "phone_number", 0.9)])
        self.assertEqual({models.LABELS[label] for _, _, label, _ in spans}, {"NAME", "ADDRESS", "PHONE"})

    def test_every_label_asked_of_gliner2_maps_to_a_type(self):
        self.assertEqual([q for q in models.GLINER2_QUERY_LABELS if q not in models.LABELS], [])


class RegistryTests(unittest.TestCase):
    def test_every_model_names_its_licence_and_source(self):
        for mid, m in models.MODELS.items():
            with self.subTest(model=mid):
                self.assertTrue(m.licence and m.source.startswith("https://huggingface.co/"))
                self.assertIn(m.backend, models.BACKENDS)

    def test_only_permissive_models_are_defaults(self):
        for mid in models.DEFAULTS:
            with self.subTest(model=mid):
                self.assertIn(models.MODELS[mid].licence, models.PERMISSIVE)
        self.assertNotIn("iiiorg/piiranha-v1-detect-personal-information", models.DEFAULTS)
        self.assertNotIn("nvidia/gliner-PII", models.DEFAULTS)

    def test_an_opt_in_model_needs_its_terms_accepted(self):
        with self.assertRaisesRegex(models.TermsNotAccepted, "cc-by-nc-nd-4.0"):
            models.check_terms(["iiiorg/piiranha-v1-detect-personal-information"], accepted=())
        models.check_terms(["iiiorg/piiranha-v1-detect-personal-information"],
                           accepted=("iiiorg/piiranha-v1-detect-personal-information",))
        models.check_terms(list(models.DEFAULTS), accepted=())

    def test_an_unknown_model_is_named(self):
        with self.assertRaisesRegex(KeyError, "no/such"):
            models.check_terms(["no/such"], accepted=())

    def test_without_the_extra_the_tool_says_so(self):
        msg = models.unavailable_reason(lambda name: False)
        self.assertIn("uv sync --project redact --extra models", msg)
        self.assertIsNone(models.unavailable_reason(lambda name: True))


if __name__ == "__main__":
    unittest.main()
