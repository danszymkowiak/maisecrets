# maisecrets rule benchmark

Measures the detection rules against public labelled datasets. The design is in
`docs/BENCHMARK.md`; this folder is developer-only and never part of the plugin release.

```bash
uv run --project bench python -m unittest discover -s bench/tests   # the bench's own tests
```

The data lives outside the repository: `$MAISECRETS_BENCH_DATA`, default `~/.cache/maisecrets-bench`.
Setup and run commands follow with TASK-11.8 and TASK-11.9.
