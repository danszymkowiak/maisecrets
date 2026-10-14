# redact: document redaction before a language model sees the text

**Decided with the user on 2026-10-12 (TASK-34).** `redact` is a command the user runs as data
prep: it extracts the text of documents known to hold personal data (PDF, CSV, Excel, HAR, vCard,
iCalendar, plain text; one file or a whole directory) and redacts it before the text goes to
Claude. The plugin redacts in the moment, fast and light; `redact` can afford local models and a human review,
because nobody waits for it in a prompt.

## What it never does

- It never changes the plugin. It lives in `redact/`, its own uv project (like `bench/`), and
  imports the plugin's detector from the same checkout; `maisecrets/` and `hooks/` import nothing
  of it and nothing outside the standard library (`redact/tests/test_skeleton.py`).
- It never sends text anywhere. Models run locally on the CPU; nothing goes to a remote API.
- It never reads the plugin's store or vault, and never modifies or overwrites its input.
- It never writes an output it could not redact: with no detector available it refuses.

## Pipeline

Pure functions (`redact/maisecrets_redact/pipeline.py`); the CLI only reads and writes files.

1. **Extract** (TASK-34.2): a document becomes text plus a map from text offsets back to its
   source (PDF page; sheet, row and column), and a table keeps where each cell lies in that text.
   Digital PDFs only, no OCR.
2. **Detect**: the plugin's deterministic rules first (TASK-34.3: secrets, IBAN, cards, e-mail,
   phone, country IDs, the terms file), then local PII models for what rules cannot find, such
   as names and free-form addresses (TASK-34.4, an optional extra). The models read the text
   with every rule hit already replaced by `[TYPE]`, so they never see a value the rules found;
   their spans map back to the original text. A span is cut at each cell (and page) edge, so a
   table row keeps its columns, and a model's e-mail without an `@` is dropped: gliner2 calls
   the city after an `[EMAIL]` cell an e-mail (TASK-49). A table's header counts as a rule: every
   cell under `password`, `client_secret`, `api_key` and the like is a SECRET, under `username` or
   `login` a USERNAME, so a browser or password-manager export comes out without its passwords.
   Headers match by their words, so `login_username` is a USERNAME, while `token` (an NLP column)
   and a flag such as `isSecret` stay plain (TASK-56). A TOTP or `otpauth` column is a SECRET (a
   2FA seed), and a header that names a personal type makes a column hit too (TASK-51): NAME
   (`first_name`, `surname`, `customer_name`), DOB, NATIONAL_ID (`ssn`, `ahv`), PASSPORT, TAX_ID,
   ACCOUNT (`iban`, `account_number`), PHONE and ADDRESS (`street`, `address_line_1`, not
   `email_address` or `ip_address`). `name`, `account`, `title` and `city` alone stay plain: a
   password manager names its entries so. A notes column goes to the models. A HAR file (a
   browser's record of a session, TASK-52) is read field by field (`entry 3, request header
   Cookie`): every cookie, the Cookie, Set-Cookie, Authorization and Proxy-Authorization headers,
   a header named like a secret (`X-Api-Key`), and a query or form value under a name such as
   `access_token`, `password` or `user` are hits; URLs and other headers stay, text bodies go to the
   rules and models, and image, script and style bodies are left out. A vCard or iCalendar file
   (TASK-53) is unfolded and read property by property (`card 2, field TEL`, `event 1, field
   ATTENDEE CN`): FN, N and a CN parameter are a NAME, TEL a PHONE, EMAIL, ORGANIZER and ATTENDEE
   an EMAIL, ADR and LOCATION an ADDRESS, BDAY a DOB; a meeting passcode in NOTE, SUMMARY or
   DESCRIPTION (`?pwd=`, `Passcode: ...`) is a SECRET, and the rest of the free text goes to the
   rules and models. Photos, logos, sounds and keys are left out. A model span
   on a GUID under an id header (`guid`, `uuid`, `id`, `customer_id`), or labelled an account or a
   national id in a table cell, is dropped, and so is one on a 10- or 13-digit timestamp under a
   time header (TASK-50); a GUID anywhere else goes to review even when the models agree, since it
   may be a UUID-shaped key (TASK-57).
3. **Decide** (TASK-34.5, TASK-34.8): a deterministic hit is redacted; a model span is redacted
   when two of the four default models find it, and goes to a person's review otherwise, except a
   span only openai/privacy-filter finds, which is dropped (`models.VOTE_K`, `models.NOT_REVIEWED`).
4. **Render** (TASK-34.6, TASK-54): a PDF or text file becomes `<file>.redacted.txt`; a CSV or TSV
   becomes `<file>.redacted.csv` with the input's delimiter and its header row, and a workbook one
   `<file>.<sheet>.redacted.csv` per sheet. Each cell is redacted on its own (no span crosses a cell)
   and a cell holding the delimiter, a quote, a tab or a line break is quoted, so a row keeps its
   columns. A sheet name unsafe in a file name is made safe; a sheet whose name was redacted is named
   by its number (`sheet2`). The outputs go next to each file, or into a mirrored tree under `--out`,
   with placeholders of the plugin's kind (one value, one placeholder, across the run). A workbook
   is written whole or not at all: if one of its sheet outputs exists, none is written.

Reversible mode (`--reversible`, a vault of the placeholder map, TASK-34.7) is not built: the
user has no health-data use case for it (2026-10-13). A hook that redacts on read is out of scope: a post-read hook fires after the
text is already in the model's context.

## Use

```bash
redact statement.pdf                    # writes statement.pdf.redacted.txt next to it
redact lohn.xlsx --regions ch --drop-column Name   # writes lohn.xlsx.<sheet>.redacted.csv per sheet
redact notes.txt --out ~/prep           # writes ~/prep/notes.txt.redacted.txt
redact ~/tax-2025 --recursive           # writes each file's output next to it
redact ~/tax-2025 -r --out ~/prep/tax   # mirrors the tree into ~/prep/tax/
```

A directory run redacts every supported file and writes each output next to its file, in the same
folder (user, 2026-10-14), or mirrors the tree into `--out`; subfolders only with `--recursive`.
An earlier output (`*.redacted.txt`, `*.redacted.csv`) is never taken as input, so a second run
redacts nothing again. Unsupported files, a PDF without text and a link that points outside the tree are skipped with one
line each; an `--out` folder inside the source tree is refused (the source folder itself is the
default); an output that exists is kept. One value keeps one placeholder across the whole run.

Each value becomes a placeholder of its type (`⟦IBAN_1⟧`, `⟦SECRET_2⟧`); the same value keeps the
same placeholder across a run. Without `--regions` the country rules of the person's maisecrets
config apply (it is only read), and the plugin's personal terms file applies too. An existing output
is never overwritten, and the input is never changed. The summary names counts per type, never a value.

## Review

With the model extra installed, a span the models disagree on goes to you. At a terminal `redact`
asks for each (redact or keep), showing its position, its type, which models found it and the
surrounding words, with every value masked. Without a terminal it writes
`<output>.review.json` with the same items and `"decision": null`; set each to `"redact"` or
`"keep"` and run again. Nothing is written while a decision is open (exit code 3), unless
`--no-review` redacts every disputed span. A review file belongs to one version of the document:
if the document changes, it is refused as stale.

## Password shape (TASK-55, 2026-10-14)

A password with no context, such as one in a password manager's notes column, matches no rule,
header or model. Entropy does not find it either: human passwords score low, and GUIDs, hashes
and timestamps score high. So in free text (a text file, a PDF page, a column headed `notes`,
`comment`, `description`, `extra` or the like, a vCard NOTE or an event DESCRIPTION) every token
of 8 to 64 characters with three of lower case, upper case, digits and symbols is checked
against the shapes that are not passwords: ids and hashes, dates, numbers and amounts, versions
and references (`ISO-9001`), codes (`2024-Q1-05`), a word with digits (`Version2024`), words and
punctuation (`Jean-Pierre`, `Hello,World`), identifiers, URLs, mail addresses, paths, `key=value`,
markup and the plugin's placeholders. What is left is a review item, never a redaction of its
own; at a terminal you are asked, otherwise it waits in the review file.

`uv run --project redact --with pyarrow python -m maisecrets_redact.measure --password-shape check`
measures it on the bench text; the shapes above were set on the dev split, and on the check
split they give:

| dataset | words | labelled passwords found | false hits per 1,000 words |
|---|---|---|---|
| Nemotron-PII | 3.9 M | 1,557 of 2,090 (74 %) | 0.02 |
| Gretel (finance) | 2.2 M | 136 of 216 (63 %) | 0.45 |
| TAB (court decisions) | 0.5 M | none labelled | 0.02 |
| findocs | 0.09 M | none labelled | 0 |
| Mendeley | 2.2 M | none labelled | 0 |

Over all five, 1,693 passwords found against 1,056 false hits, so the check is kept. Most of
Gretel's false hits are structured finance messages (SWIFT and EDI segments) that prose and a
notes column rarely hold; a hit on a value that is no password costs one "keep" in the review.

## Models on the bench (TASK-34.8, 2026-10-12)

`uv run --project redact --with pyarrow python -m maisecrets_redact.measure` runs the rules and then
each model, as the tool does, on 150 documents from each of four bench datasets (findocs, Gretel,
Nemotron-PII, Mendeley; `docs/BENCHMARK.md`): run 20261012-191234, offsets only, under the bench's
data directory. A value counts as hidden when redacted spans cover 80 % of it. A false redaction is
a span that touches no positive gold value, counted per 1,000 words. A review item is a span the
vote leaves to a person.

**What the second step adds.** The rules hide 973 of the 2,746 scored values (IBAN, AHV, SSN,
e-mail, most phones and accounts) and nearly no names, addresses or birth dates. The models read the
text with those values already replaced and work on the 1,773 left.

| configuration | names | addresses | birth dates | phones | accounts | false / 1k words | review / 1k words |
|---|---|---|---|---|---|---|---|
| rules alone | 0% | 0% | 0% | 79% | 89% | 0.3 | 0 |
| rules, then the defaults, 2 of 3 agree | 83% | 89% | 97% | 100% | 98% | 6.0 | 25 |
| rules, then the defaults, all 3 agree | 60% | 71% | 70% | 95% | 92% | 2.5 | 36 |
| rules, then all four models, 2 of 4 agree | 88% | 90% | 100% | 100% | 98% | 7.2 | 25 |
| the same, a span only privacy-filter found dropped, not reviewed | 88% | 90% | 100% | 100% | 98% | 7.2 | 9 |

**Why these three models.** The vote is only worth something when the models fail on different
values. Over the 1,773 values the rules leave, the misses of each pair correlate (phi):

| pair | phi of misses | both miss |
|---|---|---|
| urchade / fastino | 0.58 | 213 |
| urchade / knowledgator | 0.39 | 192 |
| urchade / privacy-filter | 0.35 | 141 |
| fastino / privacy-filter | 0.33 | 160 |
| knowledgator / fastino | 0.31 | 206 |
| knowledgator / privacy-filter | 0.30 | 184 |

The defaults are all four models with a 2-of-4 vote, and a span only openai/privacy-filter finds
is dropped rather than asked about (the user's choice, 2026-10-12): the last row of the first
table. privacy-filter is a token classifier, another architecture than the three GLiNER models,
and its misses overlap least with theirs; it also makes the most false redactions, which alone
were most of the review questions. Its low score on birth dates in the first measurement was a
label the tool did not map (`private_date`), now fixed.

## Install

```bash
uv tool install --python 3.12 --editable ./redact     # puts `redact` on PATH, imports the detector from this checkout
uv tool install --python 3.12 --editable './redact[models]' --force   # with the local PII models
redact --help
uv run --project redact python -m unittest discover -s redact/tests
```

Python 3.12: torch warns that its script compiler is unsupported on 3.14, and uv takes the newest
Python it finds unless told. Once the models are complete in the local Hugging Face cache, a run asks
no server at all (`HF_HUB_OFFLINE`, set by the tool unless you set it yourself); the first run downloads
them. Complete means each snapshot holds its config and weights, and a GLiNER model without a
tokenizer of its own also has its base encoder's config (TASK-58); a load that still fails offline
says so and asks for one run with `HF_HUB_OFFLINE=0`. A GLiNER model drops every word past its 384th, so its chunks hold at most 320 words.

`MAISECRETS_REPO` points the tool at another checkout. Dependencies and model licences are listed
in `redact/README.md`; every one must hold for any user of the public repository, and a
restrictive one is opt-in.
