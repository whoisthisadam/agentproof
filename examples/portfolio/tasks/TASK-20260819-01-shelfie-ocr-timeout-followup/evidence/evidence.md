# Evidence: TASK-20260819-01-shelfie-ocr-timeout-followup

## Summary

The OCR client now times out at 8 s, retries once, opens a circuit breaker after 5 failures in 60 s and queues receipts for later. On staging, a simulated hang returns `ocr_unavailable` in 8.4 s, the open circuit fails in 12 ms, and queued receipts were processed once the fault was cleared. Status: done.

## Commands and observations

```text
# 7 days of OCR latency from logs (2026-08-12..18), excluding the outage window
p50 1.1 s   p95 2.8 s   p99 4.9 s   n = 18,402

$ firebase use
Active Project: shelfie-staging
$ firebase deploy --only functions:scanReceipt,functions:processOcrQueue
✔ functions[scanReceipt(europe-west1)] Successful update operation.
✔ functions[processOcrQueue(europe-west1)] Successful create operation.

$ ./scripts/call-scan.sh staging fixtures/receipt-grocery.jpg              # fault flag off
{"status":"ok","items":14} in 1.3 s

$ OCR_FAULT=hang ./scripts/call-scan.sh staging fixtures/receipt-grocery.jpg   # x6
1-5: {"error":"ocr_unavailable","queued":true} in 8.4 s / 8.3 s / 8.6 s / 8.4 s / 8.5 s
6:   {"error":"ocr_unavailable","queued":true,"circuit":"open"} in 0.012 s

$ ./scripts/fault.sh staging off && sleep 90 && ./scripts/queue-status.sh staging
queued: 0, processed in last 5 min: 3
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Fails within 10 s on hang | call with fault flag | `ocr_unavailable` < 10 s | 8.3–8.6 s | PASS |
| 2 | Circuit opens | 6th call | < 100 ms | 12 ms | PASS |
| 3 | Queue drains after recovery | queue status | 0 queued | 0 queued, 3 processed | PASS |
| 4 | Normal scans work | call without fault | ok | ok, 1.3 s | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Other functions | deploy output lists only the two named functions | yes |
| Production | `firebase use shelfie-prod && firebase functions:list` (read only) | previous build, unchanged |

## Not verified

- iOS app message text on a device: checked on Android only; the text comes from the same Dart code.

## Knowledge updated

- `knowledge/shelfie/00-overview.md`: facts `receiptlens_p95_latency`, `ocr_client_timeout`.

## Follow-ups

- none
