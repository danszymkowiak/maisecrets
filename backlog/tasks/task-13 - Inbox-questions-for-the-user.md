---
id: TASK-13
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 08:27'
updated_date: '2026-10-11 09:37'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 08:27
---
TASK-11: which labelled sets should the precision/recall scorecard use, and how should their labels map onto our policy? Options: (a) synthetic only: ai4privacy PII + Presidio-generated data, plus a hand-made secret set; (b) add Samsung CredData (real leaked credentials, kept outside the repo, script prints counts only); (c) also SecretBench/i2b2 (access by request or a data-use agreement). I recommend (a) then (b) because (a) has no licence or leak risk and gives recall numbers at once, and CredData adds real secret shapes; its fixture labels (e.g. hunter2) need mapping to NO_HIT. Also: should terms.txt get its own labelled set (Polish names with inflection)?
---

created: 2026-10-11 09:05
---
TASK-7: may I push main to origin? 10 commits are ahead (terms TASK-2..5, the PDF/image ask TASK-6, README + C25 beliefs TASK-7). Every check passes (1110 tests on 3.12 and 3.9, replay 108/108, scan, counts, lint, ruff) except the harness scenario plugin_folder_moved_guarded, which fails on main too (TASK-12: likely the harness's guard.json on a machine with an account but no synced copy). Options: (a) push now, CI runs as root without an account file, where the scenario passes; (b) wait until TASK-12 is fixed. I recommend (b) because AC2 asks for a green harness and TASK-12 is next in the run; answer (a) if you want CI feedback sooner. Note: CLAUDE.md says origin is GitLab and a merge to main releases; this is a fork, so please confirm which remote 'origin' is meant (TASK-10 describes the fork's setup).
---

created: 2026-10-11 09:37
---
Update to the TASK-7 push question: TASK-12 is fixed (harness failures 0), so option (b) is satisfied. 14 commits are now ahead of origin/main, including TASK-9 (Python floor 3.12) and TASK-10 (CLAUDE.md fork notes). origin is the GitHub fork; a push to main starts .github/workflows/ci.yml (Windows + macOS). Just answer yes or no to the push.
---
<!-- COMMENTS:END -->
