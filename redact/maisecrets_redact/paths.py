"""Where the maisecrets checkout is: the tool imports the plugin's detector from it (one detector, one set of rules)
and is installed from the same checkout (uv tool install --editable ./redact). MAISECRETS_REPO overrides."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def repo() -> Path:
    env = os.environ.get("MAISECRETS_REPO")
    return Path(env).expanduser().resolve() if env else Path(__file__).resolve().parents[2]


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
