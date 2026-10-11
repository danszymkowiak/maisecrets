# Personal terms (fork)

The detector finds shapes: tokens, keys, e-mail addresses, IBANs. A name, a street or a case
number has no shape, and the README says so ("Names are not detected"). This fork adds a list
of terms that the person writes and that the detector treats like a shape: a term in a prompt,
a tool result or a transcript is replaced by a placeholder of its entity. It also asks before
the agent reads a PDF or an image, the one route by which a document reaches the model without
passing the redactor.

This note records the design. The tasks that build it are TASK-2 to TASK-7 in `backlog/`.
Upstream does not have it; TASK-8 proposes it there.

## The term file

- `terms.txt` in the maisecrets home folder (`~/.maisecrets/terms.txt`, or `$MAISECRETS_HOME/terms.txt`).
- Mode `0600`. The loader refuses a file that the group or others can read (on Windows, and for
  root in CI, the check follows the rules of the store files) and fails closed: every hook then
  answers as for a broken config, and the message names the file and its mode, never a line.
- Never read into a session. The home folder is under C8: Read, Grep, the editing tools, an MCP
  path argument and a Bash command that names the home are denied, so the agent cannot open the
  file, and maisecrets never prints a line of it. `/maisecrets:status` and `/maisecrets:list`
  show the number of entities and their labels, nothing else.
- One entity per line:

  ```
  # label      variants, separated by |
  PERSON_A     Jan Kowalski | Kowalsk* | Jan
  ADDRESS_A    ul. Przykladowa 12 | Przykladow*
  CASE_A       *sygn-0042*
  ```

  The label comes first and is separated from the variants by whitespace. Blank lines and lines
  that start with `#` are ignored; whitespace around a label and a variant is trimmed.
- A label is upper-case letters and underscores (`[A-Z][A-Z_]{0,31}`), no digits: it becomes the
  type part of a placeholder, and the placeholder grammar (`maisecrets/placeholder.py`) allows no
  digit there. A label must not be a type the detector already uses (`SECRET`, `EMAIL`, `PHONE`,
  `IBAN`, `CARD`, `IP`, …; the loader takes the list from the rules) and must be unique in the file.
- The label is shown to the model. It must not hold the term itself: `PERSON_A`, not `KOWALSKI`.

## Match modes

Each variant chooses its mode with `*` at its ends. "Letter or digit" means a Unicode letter or
digit (`[^\W_]`); an underscore, an apostrophe, a hyphen and punctuation are not.

| variant | mode | matches | does not match |
|---|---|---|---|
| `Jan` | standalone: no letter or digit on either side | `Jan`, `Jan,`, `(Jan)`, `Jan's`, at the start or end of a line or a table cell | `January`, `Janek`, `Dajan` |
| `Kowalsk*` | word start, any ending | `Kowalski`, `Kowalskiego`, `Kowalskiej` | `Nowakowalski` |
| `*kowalski` | any start, word end | `Kowalski`, `JanKowalski` | `Kowalskiego` |
| `*kowalski*` | anywhere | `kowalski` inside any run of letters and digits, also inside an e-mail address or a file name | — |

- Case-insensitive, Polish and other non-ASCII letters included (`ŁÓDŹ` matches `łódź`).
- Whitespace inside a variant matches any run of whitespace, line breaks and tabs included:
  `Jan Kowalski` matches a name that a PDF extraction broke across two lines.
- Regex characters in a variant are literal: `ul. Przykladowa 12` matches a dot, not any character.
- The whole run is replaced: for `Kowalsk*` the ending (`-iego`), for `*…*` the letters and digits
  on both sides, up to the first character that is neither.
- Longest variant wins, across all entities: `Jan Kowalski` is one match of `PERSON_A`, not `Jan`
  and `Kowalski`. Variants are tried longest first in one compiled alternation.
- An anywhere-variant (`*x*`) shorter than 4 characters between its stars is refused at load: `*an*`
  would replace half of every text. The error names the line number only. The loader also refuses
  a line with no label, a label of the wrong shape, an empty variant (`a || b`, a lone `*`) and a
  duplicate label; every message names the line number and never the text of the line.

## Placeholders

- One placeholder per entity, the same in every document and every session:
  ⟦PERSON_A_c0⟧. The key is the label with the index `c0`. The placeholder grammar needs the
  `_cN` part, and the vault mints from `c1` up, so `c0` never meets a minted key. No display part:
  any part of the term would show the term.
- The placeholder is derived from the label, not minted by the vault: no counter, no TTL, no
  entry per spelling. `Kowalski`, `Kowalskiego` and `Jan Kowalski` all become the same placeholder.
- Resolve: in a tool call (Bash, MCP, the file tools) the placeholder is put back as the entity's
  first variant without a `*`, under the rehydration policy (C16) and the gates C4 (the session
  saw the term: a prompt, a tool result), C7 and C9 (the audit line names the key). An entity
  whose variants all carry a `*` has no form to put back; its placeholder is refused with a reason
  that names the label. The value comes from `terms.txt` at the call; it is never copied into the store.
- An inflected form comes back in its first form: `Kowalskiego` in a document returns as
  `Jan Kowalski` in a file the agent writes. The person fixes the grammar, or writes the
  placeholder where the exact form matters.

## Where the terms run

- One more rule source in `detect.rules()`, after the secret rules and the PII rules: a shape
  claims its span first. A token or an e-mail address that holds a term goes whole under its own
  placeholder (an e-mail's display shows at most two letters of a free-mail address and hides a
  company domain); a term that stands alone goes under its entity's placeholder.
- So the term follows every path of the detector: C1 (the mod rewrites the prompt, otherwise the
  prompt is blocked and `/maisecrets:send` sends the rewrite), C2 (tool results), C3 (the
  transcript scrub), C19 (a subagent report is checked like any text) and C24 (an incident
  record holds codes only).
- A term is not a label-rule value: there is no fixture exemption in test code and no weak word.
- No `terms.txt`: the rule source is empty and the plugin behaves exactly as upstream.
- The file is read once per hook process, like the other rule files.
- Writing this note met the resolver: a file tool that writes a placeholder resolves it, and an
  unknown key is refused. Docs and tests that show a term placeholder spell its brackets so that
  the written text holds no placeholder (here they were put in after the write).

## PDF and image reads

Claude Code's Read of a PDF or an image hands the model the document itself, not text. The
`PostToolUse` hook cannot rewrite a document block, so neither a shape nor a term in it is
redacted. Therefore:

- `PreToolUse` on Read of `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.tif`, `.tiff`
  (extension in any case: `.PDF`) answers `ask`, which prompts in auto mode too. Other files are
  unchanged.
- The prompt says what each answer means: approving sends the file to the model unredacted;
  denying lets the agent extract its text locally, and that text passes the redactor.
- The model learns the local route from the session-start context (the reason of an `ask` is
  shown to the person, not to the model): `pdftotext -layout file.pdf -` for a PDF, `tesseract
  image.png - -l pol+eng` for an image (Debian, Ubuntu: `apt install poppler-utils tesseract-ocr
  tesseract-ocr-pol`). Their output is a Bash result and passes C2 with the terms.
- Codex has no `ask` for this hook; it gets a deny whose reason names the same commands.
- A headless run (`claude -p`) refuses every ask, so a PDF Read is refused there.

## Threat-model entry (C25)

The row below joins the table in `docs/THREAT-MODEL.md` when the code and its belief exist
(TASK-7); a control there must have a test that goes red without it.

| # | control | defends against | ends where |
|---|---|---|---|
| C25 | personal terms (fork): `terms.txt` (0600, in the home, under C8) lists entities and their variants; the detector replaces a matched run by the entity's placeholder (key `LABEL_c0`) in prompts, tool results and transcripts, through the paths of C1 to C3; a placeholder resolves to the entity's first plain variant under C4, C7, C9 and C16; a Read of a PDF or an image asks first (Codex: deny) and names a local extraction that passes C2 | A1 seeing a name, an address or a case number that has no shape | a spelling the file does not list (a typo, a nickname, a transliteration such as `Kowalsky`, a declined form of a standalone variant); a term split by a hyphen or markup (`Kowal-<br>ski`); a term inside a span that a shape claimed first goes with that shape's display; a PDF or image Read the person approves, which reaches the model unredacted; a tool result above 50K characters that Claude Code writes to a file (as for C2); a document read by a tool other than Read (an MCP server that returns an image or a document); the label, which the model sees; the inflection of a resolved placeholder |
