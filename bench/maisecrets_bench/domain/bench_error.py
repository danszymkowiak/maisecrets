"""The error of the bench: a setup or run problem the person must fix (TASK-62: from paths.py, so the domain can raise
it)."""
from __future__ import annotations



class BenchError(Exception):
    """A setup or run problem the person must fix; the message names it, never a value."""
