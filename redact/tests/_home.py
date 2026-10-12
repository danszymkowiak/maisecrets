"""Imported first by every test that touches maisecrets: a temp MAISECRETS_HOME, never the person's real one."""
import os
import tempfile

HOME = tempfile.mkdtemp(prefix="redact-test-home-")
os.environ["MAISECRETS_HOME"] = HOME
os.environ["MAISECRETS_LOCALE"] = "en_US"
