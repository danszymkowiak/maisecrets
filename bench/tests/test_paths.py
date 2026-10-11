"""The data directory of the benchmark (docs/BENCHMARK.md, Layout): from the environment or a default in the user's
cache, and never inside the repository, so no dataset can be committed or scanned by accident.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from maisecrets_bench import paths


class DataDirTests(unittest.TestCase):
    def test_the_environment_names_the_data_dir(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"MAISECRETS_BENCH_DATA": d}):
            self.assertEqual(paths.data_dir(), Path(d).resolve())

    def test_the_default_is_in_the_user_cache(self):
        env = {k: v for k, v in os.environ.items() if k != "MAISECRETS_BENCH_DATA"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(paths.data_dir(), (Path.home() / ".cache" / "maisecrets-bench").resolve())

    def test_a_data_dir_inside_the_repository_is_refused(self):
        inside = paths.REPO / "bench" / "data"
        with mock.patch.dict(os.environ, {"MAISECRETS_BENCH_DATA": str(inside)}):
            with self.assertRaises(paths.BenchError) as cm:
                paths.data_dir()
        self.assertIn("inside the repository", str(cm.exception))

    def test_the_repository_root_is_the_plugin(self):
        self.assertTrue((paths.REPO / "maisecrets" / "detect.py").is_file())


if __name__ == "__main__":
    unittest.main()
