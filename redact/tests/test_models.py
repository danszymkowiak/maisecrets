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
