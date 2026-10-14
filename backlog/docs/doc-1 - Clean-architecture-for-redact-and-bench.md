---
id: doc-1
title: Clean architecture for redact and bench
type: other
created_date: '2026-10-14'
---

# Clean architecture for redact and bench, enforced by import-linter (TASK-62)

Status: approved for implementation by the user on 2026-10-14, after an independent review instead of the user's
own ("launch an independent subagent to review it, after that implement the changes"). This revision takes in every
finding of that review.

## What the user asked

- import-linter as a dev dependency of `redact/` and `bench/`, run by the git hooks and listed in the checks of
  CLAUDE.md.
- Classic clean architecture: **domain**, **application** and **adapters**, with **ports**.
- Adapters independent of each other.

## Decisions

1. The tests keep every expected value. Their imports and module qualifiers change (`pipeline.render` becomes
   `text.render`); no compatibility shim stays at an old path.
2. Composition facades keep the signatures the tests and the CLI use today (`run_file(src, target,
   model_detectors=..., regions=..., interactive=...)`, `run_dir(...)`, the bench's `run.run`, `detect_samples`,
   `setup.run`). They live in the adapters layer, build the adapter bundle and call the application. Like the
   drivers, they are left out of the independence contract.
3. The plugin (`maisecrets/`, `hooks/`) is not touched.
4. The bench's top-level scripts (`bench/*.py`) and both test folders stay outside the contracts. They are drivers;
   their imports change with the moves.
5. Each package keeps its name. `maisecrets_redact/__main__.py` stays at the package root (it imports the CLI from
   the adapters), so `python -m maisecrets_redact` keeps working. The console script entry changes to
   `maisecrets_redact.adapters.cli:main`; an editable `uv tool install` needs one reinstall (said in docs/REDACT.md).
6. Paths into the checkout (redact's `repo()`, the bench's `REPO`, `gold_exceptions.json`, `learned_table.py`) are
   computed from a named anchor, not from a parent count, so a move cannot break them silently; tests check them.
7. The bench's cache keys stay honest: a dataset adapter's `version()` hashes its own file and the domain modules it
   builds on (the generator). The first setup after the move rebuilds synthetic and findocs once. AC #4 compares the
   metrics of a full run before and after, without the manifest's version strings.

## The rule

```
adapters  ──▶  application  ──▶  domain
   │               │
   └── implement ──┴── ports (Protocols, in application/ports.py)
```

- **domain**: data types and pure functions. No I/O, no clock, no environment, no process, no third-party import,
  no import of the plugin. The contract forbids `os`, `time`, `tempfile`, `subprocess`, `multiprocessing`,
  `concurrent`, `tomllib`, `importlib` and `pathlib`-free I/O is checked by review (Path as a value type is allowed).
- **application**: the use cases. It calls the domain and reaches the outside only through ports. It imports no
  adapter and no third-party library or plugin module. `time` is allowed here (a run reports its duration).
- **adapters**: files, formats, the plugin's detector, the model libraries, parquet, the process pool, the command
  line, and the composition facades.

## redact

| today | becomes | layer |
|---|---|---|
| `pipeline.py` Position, Table, Document, Span, Decision, Detector, DETECTORS, available_detectors, detect | `domain/document.py` | domain |
| `extract.py` Unsupported, NoText; the `_Builder` | `domain/document.py`, `domain/builder.py` | domain |
| `pipeline.py` within_cells, overlapping, mask, Masked, render, render_tables, to_csv, safe_names | `domain/text.py` | domain |
| `pipeline.py` header_type and its tables, cell, _token, column_spans, har_spans, card_spans, plausible, doubtful | `domain/fields.py` | domain |
| `pipeline.py` password_shaped, shape_spans | `domain/shape.py` | domain |
| `review.py` decide | `domain/vote.py` | domain |
| `review.py` Item, items, _where, _digest | `domain/review_items.py` | domain |
| `models.py` Backend, LABELS, QUERY_LABELS, GLINER2_QUERY_LABELS, WORD_RE, Model, MODELS, DEFAULTS, PERMISSIVE, VOTE_K, NOT_REVIEWED, TermsNotAccepted, check_terms, windows, merge_pieces, gliner2_spans, detector_from | `domain/models.py` | domain |
| `rules.py` Placeholders | `domain/placeholders.py` | domain |
| `app.py` output_name, the suffixes, TABLES, the choice of outputs | `domain/outputs.py` | domain |
| `app.py` run_file, run_dir, Result, DirSummary | `application/redact_file.py` | application |
| (new) | `application/ports.py` | application |
| `extract.py` (all formats) | `adapters/extract.py` | adapter |
| `rules.py` detector, `paths.py` | `adapters/plugin_rules.py` | adapter |
| `models.py` GlinerBackend, Gliner2Backend, TokenClassificationBackend, BACKENDS, REQUIRED, unavailable_reason, _QUIET, cache checks, library_env, load | `adapters/model_backends.py` | adapter |
| `review.py` read_file, write_file, StaleReview | `adapters/review_file.py` | adapter |
| `app.py` files_of, _inside, the writes | `adapters/files.py` | adapter |
| (new) run_file, run_dir with today's signatures | `adapters/compose.py` | adapter (facade) |
| `cli.py`, `measure.py` | `adapters/cli.py`, `adapters/measure.py` | adapter (drivers) |

Ports: `Extractor` (`extract(path, drop_columns)`, `supports(path)`), `Detector` (re-exported from domain),
`ModelBackend` (domain's `Backend`, re-exported; `max_words` optional), `ReviewStore` (`read(target, doc) -> dict`,
empty without a file; `write(target, doc, items, decided)`), `OutputSink` (`exists(path)`, `write(path, text)`),
`Tree` (`files(root, recursive)`, `is_link_outside(path, root)`, `inside(path, root)`, `same(a, b)`). The rules
detector is built once by the facade and passed in; `run_file` no longer builds it per call.

Contracts in `redact/pyproject.toml` (`[tool.importlinter]`):

1. layers in container `maisecrets_redact`: `adapters` > `application` > `domain`.
2. independence: `adapters.extract`, `adapters.plugin_rules`, `adapters.model_backends`, `adapters.review_file`,
   `adapters.files`.
3. forbidden for `domain` and `application` (`include_external_packages = True`): `maisecrets`, `gliner`,
   `gliner2`, `transformers`, `torch`, `pypdf`, `openpyxl`, `pyarrow`.
4. forbidden for `domain`: the standard library's I/O, clock and process modules listed above.

## bench

| today | becomes | layer |
|---|---|---|
| `schema.py` Span, Sample, OUT_OF_SCOPE, GOLD, SPLITS, validate (takes an `unknown_type` predicate) | `domain/samples.py` | domain |
| `schema.py` ARROW, read, write | `adapters/parquet_store.py` | adapter |
| `labels.py` LabelTable and parsing from a dict | `domain/labels.py` | domain |
| `labels.py` load, TABLES (the TOML files) | `adapters/files.py` | adapter |
| `floors.py` Floors, parsing from a dict (takes `unknown_type`) | `domain/floors.py` | domain |
| `floors.py` load, PATH | `adapters/files.py` | adapter |
| `split.py`, `score.py`, `floorscore.py`, `curves.py`, `rank.py`, `recommend.py`, `errors.py`, `perturb.py`, `passrate.py`, `usefulness.py`, `validators.py`, `entropy.py`, `labelclass.py`, `learned_table.py`, `audit.py` | `domain/` (same names) | domain |
| `paths.py` BenchError | `domain/bench_error.py` | domain |
| `paths.py` REPO and the data directory | `adapters/locations.py` (shared by every adapter, outside the independence list) | adapter |
| `exceptions.py` digest_text, digest, apply, FIELDS, VERDICTS | `domain/exceptions.py` | domain |
| `exceptions.py` load, FILE | `adapters/files.py` | adapter |
| `wordlike.py` chunks, coverage, bigram_table, bigram_score | `domain/wordlike.py` | domain |
| `wordlike.py` load_words | `adapters/files.py` | adapter |
| `loo.py` mutations, _toml | `domain/loo.py` | domain |
| `loo.py` write | `adapters/files.py` | adapter |
| `mutation.py` Mutation, judge, _worse, _beyond_tolerance, SETTABLE, EPS, RECALL_TOLERANCE, VERDICT_ORDER, parsing | `domain/mutation.py` | domain |
| `mutation.py` validate, _fields, _stages, stages, _carried, apply, ruleset, load | `adapters/plugin_detector.py` | adapter |
| `detector.py`; `run.py` the worker (_init_worker, _detections, _detect_chunk, _describe, _active, _require_rule_sets, POOL_CONTEXT, the pool loop); detections save and load | `adapters/plugin_detector.py`, `adapters/parquet_store.py` | adapter |
| `run.py` LANGUAGES, LOCALES, group_of, _group_config, score_all, score_tags, summarise, report, floor_report, licence_notes, GUARD, JUDGED, UNLABELLED_NEGATIVE, DROPPED, SKIP_TYPES, default_roles, default_datasets | `domain/run_report.py` | domain |
| `run.py` run (the use case) | `application/run.py` | application |
| `mutate.py`, `round.py` | `application/` | application |
| `setup.py` run, Source (the port) | `application/setup.py`, `application/ports.py` | application |
| `setup.py` the *_source factories, _git_rev, TAB_URL, default_out | `adapters/sources.py` (composition, outside independence) | adapter |
| `validgold.py` the marking (checks injected) | `domain/validgold.py`; the checks from the plugin in `adapters/plugin_detector.py` | split |
| `filters.py`, `learned.py` | `adapters/filters.py`, `adapters/learned.py` (they use the detector; outside independence: they import each other) | adapter |
| `adapters/*.py` (the datasets) | `adapters/datasets/*.py` | adapter |
| `adapters/synthetic.py` Doc, Gen | `domain/generator.py` | domain |
| (new) facades: run, detect_samples, setup.run with today's signatures | `adapters/compose.py` | adapter (facade) |

Ports: `GroupDetector` (`detect(samples, jobs, mutation) -> (detections, groups)`), `RuleIndex` (`rule_index()`),
`MutationChecker` (`validate(mutation)`), `UnknownType` (a predicate), `Source` (`name`, `version()`, `build()`,
`stats()`), `RunStore` (datasets.json, detections, reports), `SampleStore` (read, atomic write), `Manifest` (read,
write), `FloorsSource`, `ExceptionsSource`.

Contracts in `bench/pyproject.toml`:

1. layers in container `maisecrets_bench`: `adapters` > `application` > `domain`.
2. independence: `maisecrets_bench.adapters.datasets.*`, and `plugin_detector`, `parquet_store`, `files` among each
   other.
3. forbidden for `domain` and `application`: `maisecrets`, `pyarrow`, `datasets`, `huggingface_hub`, `openpyxl`.
4. forbidden for `domain`: the standard library modules listed above.

## Tooling

- `import-linter` in a `dev` dependency group of both projects (BSD-2-Clause). The check:
  `uv run --project redact --group dev lint-imports` (it reads `[tool.importlinter]` of that project) and the same
  for bench; into `.githooks/pre-commit` and the checks list of CLAUDE.md.
- User-facing text that names module paths changes with them (docs/REDACT.md, docs/BENCHMARK.md, error messages).

## Order of work

1. redact: contracts first (red), then the domain, the ports and facade, the adapters; green tests after each step;
   the 50,000-row timing test stays under its limit. One commit when the contracts pass.
2. bench: the same; then a full bench run before and after with identical metrics.
3. docs/REPO-STANDARDS.md: a short section on the layers and the check, linking this spec.
