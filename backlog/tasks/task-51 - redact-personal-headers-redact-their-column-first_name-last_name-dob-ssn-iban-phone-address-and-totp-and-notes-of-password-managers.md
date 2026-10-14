---
id: TASK-51
title: >-
  redact: personal headers redact their column - first_name, last_name, dob,
  ssn, iban, phone, address, and totp and notes of password managers
status: Done
assignee: []
created_date: '2026-10-14 06:51'
updated_date: '2026-10-14 07:38'
labels:
  - redact
dependencies: []
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follows TASK-50 (user, 2026-10-14: last_name should redact). A header that names a personal type makes every cell below it a deterministic hit, as password does: the vote no longer decides a column the file already labels. Password-manager exports (Chrome, Bitwarden, 1Password, LastPass, KeePass) add totp/otpauth (a 2FA seed: SECRET) and notes/extra (free text: to the models, not a column hit). Use synthetic rows only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Headers for NAME (first/last/full name, surname, given name), DOB, NATIONAL_ID (ssn and others), ACCOUNT (iban, account number), PHONE, ADDRESS make column hits; the header row stays
- [x] #2 totp/otpauth columns are SECRET; notes columns go to the models
- [x] #3 A synthetic export of each listed password manager comes out with no password, username or 2FA seed
- [x] #4 The bench or a fixture shows no new false hit on headers like name of a product or city
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
header_type now also returns NAME, DOB, NATIONAL_ID, PASSPORT, TAX_ID, ACCOUNT, PHONE, ADDRESS by header words; totp/otp/otpauth are SECRET; notes stay with the models. name, account, title, city alone stay plain (entry titles of password managers); email_address/ip_address are not ADDRESS. Tests: PersonalHeaderTests (incl. a fixture of look-alike headers for AC4) and PasswordManagerExportTests over six exports (Bitwarden, Chrome, 1Password, LastPass, KeePass, KeePassXC) with 2FA seeds.
<!-- SECTION:FINAL_SUMMARY:END -->
