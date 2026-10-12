"""The deterministic pass (TASK-34.3): the plugin's own rules (maisecrets.detect) on the extracted text. One detector,
one set of rules: whatever the plugin finds in a prompt, the tool finds in a document. The rule set is built from
explicit settings (TASK-27); without regions it follows the person's maisecrets config, which is only read. The
plugin's personal terms file applies too (docs/TERMS.md); its store and vault are never opened."""
from __future__ import annotations

from collections import Counter

from . import paths, pipeline
from .pipeline import Document, Span


def detector(regions: tuple[str, ...] | None = None, languages: tuple[str, ...] | None = None) -> pipeline.Detector:
    detect = paths.import_detector()
    if regions is None:
        settings = detect.settings_from_config()
    else:
        from maisecrets import regions as region_mod
        active = region_mod.resolve({"regions": [r for r in regions if r != "generic"]})
        settings = detect.Settings(regions=tuple(active.regions), languages=languages or tuple(active.languages))
    ruleset = detect.build(settings)

    def find(doc: Document) -> list[Span]:
        return [Span(m.start, m.end, m.type, "rules") for m in detect.scan(doc.text, ruleset=ruleset)]
    return find


pipeline.DETECTORS["rules"] = detector


class Placeholders:
    """One placeholder per distinct value and type across a run (a file or a whole directory): ⟦IBAN_1⟧, ⟦IBAN_2⟧."""

    def __init__(self) -> None:
        self._names: dict[tuple[str, str], str] = {}
        self._per_type: Counter = Counter()

    def placeholder(self, span: Span, value: str) -> str:
        key = (span.type, value)
        if key not in self._names:
            self._per_type[span.type] += 1
            self._names[key] = f"⟦{span.type}_{self._per_type[span.type]}⟧"
        return self._names[key]

    def counts(self) -> dict[str, int]:
        return dict(self._per_type)
