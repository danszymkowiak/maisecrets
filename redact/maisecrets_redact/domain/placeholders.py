"""The placeholders of a run (TASK-34.6): one per distinct value and type."""
from __future__ import annotations

from collections import Counter

from .document import Span


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
