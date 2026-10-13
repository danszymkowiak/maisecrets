---
id: TASK-17
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 17:43'
updated_date: '2026-10-13 09:09'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-34.8 (redact, not the plugin): which vote should redact use without asking? Measured on 600 bench documents with the new defaults (urchade, knowledgator, fastino): all three must agree (today, TASK-34.5): names 67 %, addresses 62 %, birth dates 81 %, 4.1 false redactions per 1,000 words, the rest goes to review. Two of three: names 82 %, addresses 82 %, birth dates 100 %, 8.4 per 1,000 words, and fewer review prompts. Options: (a) two of three, (b) keep all three. I recommend (a): redact runs before data goes to Claude, so a missed name is the costly error and an extra redaction is cheap; the review still catches what only one model sees. (Numbers before the findocs relabel of TASK-36, which lowers the false redactions of both.)

TASK-34.8 vote, corrected numbers after the findocs relabel (TASK-36), defaults urchade+knowledgator+fastino: all three agree: names 64 %, addresses 53 %, birth dates 73 %, 2.0 false redactions per 1,000 words. Two of three: names 83 %, addresses 85 %, birth dates 100 %, 4.4 per 1,000 words, and fewer review prompts (6.3 vs 8.7 per 1,000 words would be false if all answered yes). Recommendation unchanged: (a) two of three.

TASK-11.36 (Kaggle): the token in .env works (the competition and its files are listed; .env is now git-ignored, 8825cbf). The download is refused (403) until your account accepts the competition rules: open kaggle.com/competitions/pii-detection-removal-from-educational-data, Join Competition / I Understand and Accept. Please also paste the data licence line from its Data tab (the page needs a browser; I could not read it). Then the adapter (built meanwhile, opt-in) runs. Options: (a) accept and paste the licence, (b) drop the dataset. I recommend (a): it is the only real, human-written, human-labelled text in the bench.

TASK-11.25 (plugin normaliser): switch on ansi, cr, invisible, gutter, entity, fullwidth? Bench (clean gold, mutate-r6): accepted, narrows the SECRET_PREFIXED gap, no false positive added. Perturbation: each restores its disguise from 9-35 % to about 88 % recall. Cost: nothing on plain text; when a stage changes the text the second pass scans it again: +19 ms on 25 KB, +95 ms on 120 KB. escape stays off (+60 Gretel false alarms); unwrap stays off (too slow, TASK-37). Options: (a) switch on all six, (b) entity only (the only one the datasets themselves reward), (c) none. I recommend (a): the disguises they undo (ANSI colour, zero-width characters, CR progress lines, cat -n/grep gutters) are exactly what tool output carries, and 95 ms at 120 KB happens only when one is present.

TASK-34.8 vote, superseding my two notes above (new defaults knowledgator + fastino + privacy-filter, models run after the rules, run 20261012-191234). Gain of the model step over rules alone (names 0 %, addresses 0 %, birth dates 0 %, phones 79 %, accounts 89 %, 0.3 false/1k words): (a) 2 of 3 agree: 83 %, 89 %, 97 %, 100 %, 98 %; 6.0 false/1k words; 25 review prompts/1k words. (b) all 3 agree (today): 60 %, 71 %, 70 %, 95 %, 92 %; 2.5 false/1k; 36 prompts/1k. (c) all four models, 2 of 4: 88 %, 90 %, 100 %, 100 %, 98 %; 7.2 false/1k; 25 prompts/1k. I recommend (a): a missed name is the costly error before data reaches Claude, and (a) also asks fewer review questions than (b). (c) adds 5 points on names for 1.2 more false redactions per 1,000 words, if you prefer recall further. Either way about 25 review prompts per 1,000 words is a lot; most are privacy-filter's lone spans.

TASK-8: may I file the drafted feature request (user-defined personal terms, C25) on Mcpgate-de/maisecrets? The draft is in TASK-8's notes. Options: (a) file it as drafted, (b) edit first, (c) not now. I recommend (b) a quick read: the draft is from 2026-10-11 and the fork has changed since (Betterleaks, redact); it says nothing about those, which is right for an upstream issue, but the date and test count are stale.

TASK-38 and TASK-39 (from leave-one-out, both accepted on the bench): (38) de-vat-id#0 requires a VAT context word: its 60 hits on Gretel are FIX/XML identifiers that pass the checksum; (39) drop de-handelsregister: its hits are real company register numbers, public, not personal data. Options: approve both, one, or none. I recommend both; 39 is a judgement call (a company number is not personal, but some prefer to hide it).

TASK-34.8, your variant (all four, 2 of 4, privacy-filter's lone spans dropped, not reviewed), from the cached rules-first spans: names 88 %, addresses 90 %, birth dates 100 %, phones 100 %, accounts 98 %; 7.2 false redactions and 9 review prompts per 1,000 words (25 when they are asked). I now recommend it over 2 of 3. To ship it: urchade back among the defaults, and a vote rule redact lacks (k of N, plus a model whose lone spans are never asked about). Shall I implement it as the default?

Answered by the user 2026-10-12: redact's vote is all four models, 2 of 4, privacy-filter's lone spans not reviewed; implemented as the default (55bfff7). The TASK-34.8 vote questions above are settled.

TASK-40 (operating points, TASK-21.9): credit-card without its context-word gate and generic-api-key's entropy bar from 3.5 to 3.3. Together on the bench: +325 card numbers, +259 generic secrets, +12 bank numbers, for 167 more false positives (+0.003 weighted per 1,000 tokens). Options: (a) both, (b) cards only, (c) neither. I recommend (a): the floors put recall first, and card numbers are critical.

TASK-41 (TASK-11.21): generic-api-key's entropy bar per charset instead of one 3.5: +112 generic secrets AND 11 fewer false positives. It competes with TASK-40's flat 3.3 for that rule (more finds, +101 false positives). Options: (a) per charset (41) plus cards from 40, (b) 40 as proposed, (c) neither. I recommend (a); I would judge the combination before applying.
<!-- SECTION:NOTES:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 17:44
---
TASK-11.28..11.31: four plugin changes passed the bench (round 2, TASK-11.17): us-bank bank word just before the number (+1.10 dev / +1.15 check, within tolerance), se-personnummer and it-fiscal-code checksums (small, within tolerance), keyword rules skipping UPPER-UPPER-..._ identifiers and digits:word values (strict on dev, but zero effect on check: the shapes sit in a few dev files), drop uk-postcode (strict everywhere). Options: (a) approve all four; (b) approve some (name them); (c) none yet. I recommend (a): each gets a can-fail belief and a bench rerun; the identifier filter's dev-only evidence is the weakest, so (b) without TASK-11.30 is the cautious choice.
---

created: 2026-10-11 17:44
---
Tolerance (TASK-11.16): 'score not lower on every dataset' rejects changes over ai4privacy score drops of 0.01 points (one or two finds of ~250,000): skip UPPER_lower identifiers (+0.82 dev, CredData +2.45), us-passport and us-license context words. Options: (a) keep it as is; (b) allow a dataset's score to fall by at most 0.05 points when the mean rises; (c) allow it on guard datasets only. I recommend (b): 0.05 points is below one find per 2,000 on every scored dataset and the mean must still rise; the reports keep showing the loss.
---

created: 2026-10-11 17:44
---
TASK-11.17 family C: about 1,300 of ai4privacy's dev false alarms (email 1,005, ip 318, phone 20) are values at offset 0 of a continuation record (ids ...B, ...C) that ai4privacy's own chunking left unlabelled; another ~2,300 are values its generator wrote outside the injected slots. Options: (a) the scorer leaves a detection at offset 0 of a continuation record uncounted (neutral) and reports state that ai4privacy precision is a lower bound; (b) only the lower-bound note; (c) nothing. I recommend (a): the first group is a provable gap of the dataset; the second cannot be split from real false alarms without reading text.
---

created: 2026-10-11 21:05
---
TASK-11.32: the digest filter of TASK-11.20 passed strictly (no find lost, 7 false alarms removed, mean +0.01). Options: (a) port it to detect.py with a can-fail belief; (b) leave it in the bench and close TASK-11.32. I recommend (b): the gain is 7 false alarms over four datasets, and every new exception in detect.py has to be maintained.
---

created: 2026-10-11 23:32
---
TASK-11.34/11.35/11.37: the usefulness check (run 20261012-011327) says keep for Nemotron-PII, Mendeley and findocs; all three now run as scored datasets, and the equal-weight mean moved from 71.5% to 79.8% because of them (Mendeley 95.0%, findocs 91.6%, Nemotron 77.4%). Options: (a) keep all three scored; (b) make Mendeley a guard (its in-scope types are only SSN, phone and card, at 100% precision, and it moves on 5 of 30 probes); (c) other. I recommend (a): TASK-21 replaces the equal-weight mean anyway, and under recall floors per type Mendeley's 51,283 SSNs and 42,527 cards give the critical tiers the sample size they need.
---

created: 2026-10-11 23:39
---
TASK-21.1/21.7: bench/floors.toml weighs gretel and findocs 2.0 in the false-positive objective (every other dataset 1.0), and splits SECRET into SECRET_PREFIXED (critical, 0.999: a CredData category naming a vendor token with a fixed shape, 36 parts listed in the file) and SECRET_GENERIC (no regression: API, Key, Password, Token, CMD/CURL/SQL passwords, URL credentials, ...). Options: (a) confirm 2.0 and the split as written; (b) another weight (name it); (c) move parts between prefixed and generic (name them). I recommend (a): 2.0 makes the two finance sets count as much as two others without letting one of them decide alone, and the split puts in the critical tier only shapes a dedicated rule can find. TASK-21.1 waits for this answer; the scoring code (TASK-21.8) does not.
---

created: 2026-10-12 05:27
---
INCIDENT (2026-10-12, TASK-19.2): to run the suite with Betterleaks on, I wrote a scratch runner that called detect.rules() BEFORE the tests imported tests/_isolate.py. That imported maisecrets.vault with no MAISECRETS_HOME set, so vault.HOME, INDEX, CONFIG and SERVICE were bound to the real ~/.maisecrets for the whole run (tests/test_core.py caught it at import, 6 tests failed on 'the vault home is the one _isolate made'). tests/test_vault.py ran, and its _reset() deletes HOME/index.json, vault.json, vault.enc.json, key, audit.log, events.log and writes config.json = {"backend": "jsonfile", "allow_plaintext_store": true}. So the real store's index, encrypted vault file and key are probably gone, and the real config.json probably now selects the PLAINTEXT jsonfile backend; any secret stored since then may sit in ~/.maisecrets/vault.json in the clear. I could not check: listing ~/.maisecrets was denied, and I did not try again. Please check ~/.maisecrets (file times around 2026-10-12, the config backend), restore from a backup if you have one, and delete any plaintext vault.json. The runner is deleted. Options for preventing this: (a) a new task: vault refuses the default home when a test marker (MAISECRETS_TEST_HOME_OWNED) is set but MAISECRETS_HOME is not, plus a test; (b) only a note in docs/TESTING.md that any runner must import tests/_isolate first. I recommend (a): the guard works for any future runner, a note does not.
---

created: 2026-10-12 05:27
---
TASK-19.2: with SECRET_RULES = 'betterleaks', in-process tests that pass under gitleaks fail (about 40). Most come from two rules only Betterleaks has: generic-password (flags 'testpass', 'continue', 'self._password', ...) and generic-credential-uri (flags '%24REDIS_PASSWORD', '2026-10-08', '443' in the password slot of a URL), values the detect-secrets and url-password-no-user fixes already drop. AC #1 asks that the existing tests pass in both modes. Options: (a) let overrides.txt switch a rule off ('generic-password  off') and switch these two off until TASK-19.3 benches them, then rerun to find what remains; (b) port the matching fixes to the two rules now (ds-value, the url-password checks); (c) narrow AC #1 to 'gitleaks mode unchanged', and the Betterleaks differences become TASK-19.3's input. I recommend (a): the epic keeps a new rule only when the bench shows no precision loss, so these two are off until TASK-19.3 shows otherwise, and the fixes in (b) can follow there with evidence. (I did not get a clean list of the remaining failures: that run was the faulty one above.)
---

created: 2026-10-12 06:03
---
TASK-25: the two guards are in (commit below): tests/_isolate refuses to start when maisecrets.vault was already imported with another home, and under a test run's home marker the vault refuses the user's own ~/.maisecrets (load_config, Vault(), make_backend). tests/test_isolation_order.py replays the 2026-10-12 runner in a child with a fake user home: refused, nothing written. AC #2 (no module binds the vault home at import) is left: HOME is imported by value in about 40 places (hooks, cli, events, settings, consent_store, ssh_approval, destinations, tips, terms, hooks/dispatch.py) and many tests patch vault.HOME. Options: (a) drop AC #2, the guards cover the failure; (b) do it: a home() function read per call, every import site and the tests that patch HOME changed; (c) narrow it to a grep test that no new module imports HOME by value. I recommend (a): both entry points of the incident (the import order and the real home under a test run) now fail loudly; (b) is a wide change for no further safety.
---

created: 2026-10-12 08:20
---
TASK-23: the US (NXX) NXX-XXXX rule (region us, reserved middle-9 area codes excluded) on clean gold (run 20261012-101259 against 20261012-100249): PHONE recall findocs 50% -> 100%, Gretel 56.7% -> 63.3%, Nemotron 23.2% -> 29.7% (about 2,600 more finds); TASK-21.8 verdict: accepted (PHONE gap narrowed, no floor or guard worse). But weighted false positives per 1,000 tokens rise 0.2912 -> 0.2921 (+43: Gretel 25, Nemotron 17, ai4privacy 1), and TASK-23's AC #2 says 'not higher'. I read the 43: nearly all are real-looking phone numbers the datasets left unlabelled ('can be reached at (832) ...', 'Phone: (301) ...', a dial-in number), the rest placeholders such as (555) 555-1234 or public office numbers. Options: (a) accept: the TASK-21.8 verdict decides, the 'false positives' are missing labels; (b) keep AC #2 strict and reject the rule; (c) first teach the bench to leave an unlabelled hit of a valid shape unjudged (a new task), then judge again. I recommend (a): 2,600 finds against 43 hits that are mostly unlabelled numbers, and the verdict the bench was given says accepted; (c) is worth doing later for every type, not as a gate here.
---

created: 2026-10-12 09:27
---
TASK-11.36 (Kaggle PII Data Detection as a real-text check): needs your Kaggle account: an API token in the environment or ~/.kaggle, and your acceptance of the competition's terms on kaggle.com (the data is competition data, so it can only be opt-in like ai4privacy). Options: (a) you accept the terms and put a token in place, then I write the opt-in adapter and test it on the real data; (b) I write the adapter now against the documented format (tokens, labels, whitespace per essay) with a made-up fixture, untested on the real data until (a); (c) drop the task. I recommend (a): an adapter that never saw the real file tends to break on its first run, and the dataset's value is exactly that it is real text.
---

created: 2026-10-12 09:52
---
User, 2026-10-12: TASK-23 accept (the TASK-21.8 verdict decides; the extra hits are mostly unlabelled numbers). TASK-25: drop AC #2. TASK-11.36: the Kaggle details come later. TASK-19.2: switch generic-password and generic-credential-uri off until TASK-19.3 benches them.
---

created: 2026-10-12 10:04
---
User, 2026-10-12: accepted every recommendation of comments #1-#6. #1 approve TASK-11.28..11.31 (each re-judged on the clean gold under the floor verdict); #2 the tolerance rule is superseded by the floor verdict (TASK-21); #3 the scorer leaves a hit at offset 0 of an ai4privacy continuation record neutral and reports note that ai4privacy precision is a lower bound (TASK-33); #4 TASK-11.32 stays in the bench, closed; #5 Nemotron, Mendeley and findocs stay scored; #6 floors.toml weights (Gretel, findocs 2.0) and the SECRET split confirmed. Still open: the Kaggle details (TASK-11.36).
---

created: 2026-10-12 10:06
---
TASK-34.7 (redact --reversible): the vault that maps placeholders back to values is the most sensitive file of the tool. Options: (a) reuse the plugin's store backends (keychain on macOS, Credential Locker on Windows, encrypted file on Linux) under a separate service name per run; (b) a separate encrypted file per run (key from a passphrase or a key file), kept away from the output; (c) build it only once your friends confirm the PHI use case. I recommend (b) with (c): a per-run file can be handed over with the redacted text and deleted afterwards, unlike entries in the keychain, and the spec defers the mode until the use case is confirmed. Also: is the PHI use case confirmed?
---

created: 2026-10-13 08:48
---
TASK-42 (from TASK-11.24): port Presidio's checksums for es-nif, us-npi, se-organisationsnummer and uk-vehicle-registration into the plugin? On the bench together: 140 false positives fewer (Gretel 109, ai4privacy 21, Nemotron 10), no find lost; validators tested with Presidio's own vectors and against Presidio itself. it-vat-code and nhs are left out (each loses one phone number). Options: (a) port the four, (b) not now. I recommend (a): checksums are cheap, deterministic, and Presidio already applies them.
---

created: 2026-10-13 08:48
---
TASK-11.22/11.23: two filters for the generic keyword rules passed the floor verdict, neither ported yet. label-negative (skip a value after token_count, password_hash, tokenizer, ...): 49 false positives fewer on CredData, none lost. wordlike-90 (skip a value whose characters are over 90 % dictionary words, outside a password/secret label): 163 fewer, none lost, but the cut is read off all the data (the highest find scores 0.871) and the plugin would have to bundle a word list (SCOWL, about 700 KB, 93 ms to load in each hook run). Options: (a) port both, (b) label-negative only, (c) neither, keep them in the bench. I recommend (c), as for the digest filter (TASK-11.32): the gains are a few dozen to 163 false alarms over the whole bench, and wordlike-90's load time costs every hook call.
---

created: 2026-10-13 08:48
---
Normaliser stages, adding to the TASK-11.25 question above: two more stages are ready. decode (TASK-11.26: base64/hex runs that decode to text are scanned, a hit redacts the whole run): accepted on the datasets (+16 finds, +2 false positives), base64 recall under perturbation 47.7 % -> 63.8 %, hex 14.0 % -> 38.4 %; worst case 25 ms per text on CredData, p99 under 3 ms. unwrap with the cheaper guard (TASK-37): +4 ms on 120 KB of prose (was +517 ms), line-wrap recall 30.6 % -> 32.1 %, neutral on the datasets. Options: (a) switch on the six of TASK-11.25 plus decode and unwrap, (b) the six only, (c) none. I recommend (a): both new stages are bounded and only cost time where they find something to undo; TASK-43 (why Mendeley gains little from decode) can follow.
---

created: 2026-10-13 09:09
---
TASK-11.27 (repeat count): skipping a generic keyword-rule value that occurs 10+ times in one text passes the bench on dev and check (about 350 CredData false positives fewer, no find lost; at 3 repeats it lost 154 real passwords in Nemotron). But a debug log that prints the same password= line on every request is exactly such a text, and the filter would let that value through. Options: (a) port repeat10 into the plugin, (b) keep it in the bench only. I recommend (b): the cost of a missed secret in a log outweighs 350 false alarms, and the floor rule exists to keep that trade explicit.
---
<!-- COMMENTS:END -->
