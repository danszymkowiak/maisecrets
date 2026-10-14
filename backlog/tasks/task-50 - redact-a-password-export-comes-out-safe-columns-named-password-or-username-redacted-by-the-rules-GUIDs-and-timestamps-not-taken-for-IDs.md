---
id: TASK-50
title: >-
  redact: a password export comes out safe - columns named password or username
  redacted by the rules, GUIDs and timestamps not taken for IDs
status: Done
assignee: []
created_date: '2026-10-14 06:41'
updated_date: '2026-10-14 06:43'
labels:
  - redact
dependencies: []
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-14 on a browser password export (Firefox logins.csv: url, username, password, httpRealm, formActionOrigin, guid, timeCreated, timeLastUsed, timePasswordChanged). The password cells came out in the clear: no rule fires on a bare value and no model is asked for passwords. Meanwhile knowledgator called the {guid} a national ID, and the vote redacted the millisecond timestamps as ACCOUNT (openai/privacy-filter and gliner2 label uppercase GUIDs ACCOUNT, even fragments: measured on synthetic rows).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every cell under a secret-like header (password, passwd, pwd, passphrase, secret, token, api key, private key, and names ending in those) is a SECRET from the rules, in CSV and Excel; the header row stays
- [x] #2 Every cell under a username header is a USERNAME from the rules
- [x] #3 A model span on a GUID (braced or not, or a piece of one) is dropped
- [x] #4 A model span on a 10- or 13-digit number under a time header (timeCreated, created_at, date...) is dropped; the same number under another header is not
- [x] #5 A synthetic Firefox export through run_file: passwords and usernames redacted, URLs, GUIDs and timestamps kept
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
pipeline.header_type and column_spans: a header that names its cells' type gives deterministic hits, merged with the rules' in run_file. pipeline.plausible drops a model span whose cell (or, outside a table, run of non-blanks) is a GUID, or a 10/13-digit number under a time header. Real models on a synthetic 40-row Firefox export (2026-10-14): 40/40 passwords SECRET, 40/40 usernames USERNAME, 0/40 URLs, GUIDs and timestamps redacted, nothing to review.
<!-- SECTION:NOTES:END -->
