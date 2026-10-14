---
id: TASK-52
title: >-
  redact: HAR files - cookies, Authorization headers, tokens and form passwords
  redacted by their field names
status: To Do
assignee: []
created_date: '2026-10-14 06:51'
labels:
  - redact
dependencies: []
ordinal: 113000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A HAR (developer tools, Network, Save all as HAR) is JSON with every request and response: headers, cookies, query strings, posted form data, response bodies. Support desks ask for one; it carries session cookies and bearer tokens. The field names say what each value is. Extract it to text with positions per entry and field; Cookie, Set-Cookie, Authorization, Proxy-Authorization and token-like header, query and form names are deterministic SECRET hits; bodies go to the rules and models.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A synthetic HAR comes out with no cookie value, bearer token or posted password; URLs and other headers stay
- [ ] #2 Positions name the entry and field, so a review item says where it is
<!-- AC:END -->
