---
id: TASK-56
title: >-
  redact: header matching - login_username is missed, a token or isSecret column
  is taken for secrets, candidate for a time
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
labels:
  - redact
dependencies: []
priority: high
ordinal: 117000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14 (medium), confirmed: header_type('login_username') and ('db_user') give None, so a Bitwarden export (login_uri, login_username, login_password) keeps its usernames; header_type('token') and ('isSecret') give SECRET, so an NLP table's token column or a boolean flag column is wiped and cannot be reviewed; _time_header is true for candidate, mandate, lifetime, validate, so a 10-digit phone a model finds under such a header is dropped. Match headers by words (split camelCase, _ - space) instead of by suffix of the squashed name.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 login_username, db_user, email_username, account_login are USERNAME
- [ ] #2 token, token_count, isSecret, secretary stay plain; access_token, client_secret, api_token stay SECRET
- [ ] #3 candidate, mandate, lifetime, validate are not time headers; timeCreated, created_at, date, last_modified are
- [ ] #4 Synthetic exports of Bitwarden, Chrome, 1Password, LastPass and KeePass have every username and password redacted
<!-- AC:END -->
