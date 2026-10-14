"""The plugin's deterministic rules (TASK-34.3), imported from the maisecrets checkout this tool lives in, or the one
MAISECRETS_REPO names."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from ..domain.document import Detector, Document, Span


def detector(regions: tuple[str, ...] | None = None, languages: tuple[str, ...] | None = None) -> Detector:
    detect = import_detector()
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


def checkout() -> Path:
    """The checkout this file is in: the nearest folder above it with maisecrets/detect.py (TASK-62: a fixed count of
    parent folders broke silently when the module moved)."""
    here = Path(__file__).resolve()
    return next((p for p in here.parents if (p / "maisecrets" / "detect.py").is_file()), here.parents[3])


def repo() -> Path:
    env = os.environ.get("MAISECRETS_REPO")
    return Path(env).expanduser().resolve() if env else checkout()


def import_detector():
    """maisecrets.detect from the checkout; a clear error when the checkout is not where the tool expects it."""
    root = repo()
    if not (root / "maisecrets" / "detect.py").is_file():
        raise RuntimeError(f"no maisecrets checkout at {root}: install the tool from the repository "
                           "(uv tool install --editable ./redact) or set MAISECRETS_REPO")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from maisecrets import detect
    return detect
