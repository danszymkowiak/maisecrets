---
id: TASK-52
title: >-
  redact: HAR files - cookies, Authorization headers, tokens and form passwords
  redacted by their field names
status: Done
assignee: []
created_date: '2026-10-14 06:51'
updated_date: '2026-10-14 07:42'
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
- [x] #1 A synthetic HAR comes out with no cookie value, bearer token or posted password; URLs and other headers stay
- [x] #2 Positions name the entry and field, so a review item says where it is
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
extract._har: each request/response field a position (entry N, request header Cookie; query and form values each their own); URL kept as is with query values as positions; form raw text not written twice; binary/script/style bodies left out. pipeline.har_spans: cookies, Cookie/Set-Cookie/Authorization/Proxy-Authorization, secret-named headers, query/form values by header_type. Tests: test_har.py.
<!-- SECTION:FINAL_SUMMARY:END -->
