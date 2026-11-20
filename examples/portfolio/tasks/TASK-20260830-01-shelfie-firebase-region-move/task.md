---
id: TASK-20260830-01-shelfie-firebase-region-move
title: Move Shelfie's Firestore to a closer region
status: cancelled
tier: 2
product: shelfie
created: 2026-08-30
updated: 2026-09-01
owner: adam
---

# Move Shelfie's Firestore to a closer region

## Goal

Cut Firestore read latency for users in North America by moving the database. Cancelled before execution: see Handoff.

Request: "Can we move Firestore closer to US users?"

## Scope

Touch:
- nothing (cancelled during planning)

## Handoff

- State now: cancelled on 2026-09-01. Firestore's location can't be changed after creation; a move means a new project, an export/import and migrating every user's auth. Measured p95 read latency for North American users was 140 ms, which isn't the bottleneck (OCR at 2.8 s p95 is). Adam decided the cost isn't worth it.
- Last command and result: latency query on 7 days of client traces, p95 140 ms.
- Next step: none.

## Related tasks

- TASK-20260819-01-shelfie-ocr-timeout-followup
