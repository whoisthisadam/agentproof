---
id: TASK-20260819-01-shelfie-ocr-timeout-followup
title: Follow-up to the receipt-scan outage - timeouts and a circuit breaker for ReceiptLens
status: done
tier: 1
product: shelfie
created: 2026-08-19
updated: 2026-08-21
owner: adam
---

# Follow-up to the receipt-scan outage: timeouts and a circuit breaker for ReceiptLens

## Goal

When the ReceiptLens OCR API is slow or down, Shelfie's `scanReceipt` function fails fast with a clear "try again later" message and queues the receipt for a retry, instead of hanging for 60 s and timing out the app. On 2026-08-18 a 40-minute ReceiptLens slowdown made every scan hang and produced 230 one-star-review-worthy errors.

Request: "Make sure a ReceiptLens hiccup doesn't take scanning down with it again."

## Scope

Touch:
- `shelfie/functions/src/ocr/**`
- `shelfie/lib/features/scan/**` (error message only)
- Firebase staging project `shelfie-staging` (deploy)

Do not touch:
- Production Firebase project: the production deploy is part of the next release
- ReceiptLens account settings or plan

Read only:
- Cloud Functions logs for 2026-08-18 in `shelfie-prod`

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `shelfie@main` | repo | clean tree | yes |
| Firebase staging | project | `firebase use` = `shelfie-staging` | yes |

## Plan

1. Measure ReceiptLens latency from 7 days of logs (tier 0).
2. Add client timeout (8 s), one retry with jitter, circuit breaker (opens after 5 failures in 60 s), and a retry queue (tier 1).
3. Deploy to staging; test with a fault-injection flag that makes the OCR client hang (tier 1).

## Rollback

- How: redeploy the previous functions build to staging (`firebase deploy --only functions` from the previous tag).
- Tested: yes, staging redeploy is routine.
- Point of no return: none.

## Acceptance criteria

- [x] With the fault flag on, `scanReceipt` returns within 10 s with error `ocr_unavailable`.
- [x] After 5 failures, the circuit opens and calls fail immediately (< 100 ms).
- [x] Queued receipts are processed once the fault flag is off.
- [x] Normal scans on staging still succeed.

## Verification

- Boundary checks: staging function calls with and without the fault flag; app on a test device.
- Negative checks: other functions unchanged in the deploy output.
- Watch afterwards: none (staging).

## Handoff

- State now: done.
- Last command and result: 2026-08-21, 3 queued receipts processed after the fault was cleared.
- Next step: none; ships with release 3.4.0.

## Related tasks

- TASK-20260914-02-shelfie-android-release-3-4-0
