# redact

Extracts the text of documents and redacts personal data and secrets in it before the text goes
to a language model. Design and rules: `docs/REDACT.md`.

```bash
uv tool install --editable ./redact
redact --help
```

## Dependencies and licences

Every dependency and model must be usable by anyone who runs the public repository; one with
restrictive terms is opt-in and named here with them.

| dependency | used for | licence | default |
|---|---|---|---|
| pypdf (6.x) | text of digital PDFs | BSD-3-Clause | yes |
| openpyxl (3.1) | Excel workbooks (values, not formulas) | MIT | yes |
| et-xmlfile (2.x, via openpyxl) | XML for openpyxl | MIT | yes |

PyMuPDF was not taken: it is AGPL-3.0, too strong a condition for a public Apache-2.0 repository.
