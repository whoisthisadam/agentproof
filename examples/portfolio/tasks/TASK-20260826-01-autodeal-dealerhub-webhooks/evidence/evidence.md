# Evidence: TASK-20260826-01-autodeal-dealerhub-webhooks

## Summary

The bot now receives DealerHub webhooks, verifies the HMAC signature over the raw body, ignores repeated event IDs for 24 h and messages the buyer. All three event types worked from the DealerHub sandbox to the staging bot. Status: done.

## Commands and observations

```text
$ dealerhub-sandbox trigger test_drive.confirmed --lead L-TEST-0042
$ dealerhub-sandbox trigger test_drive.rescheduled --lead L-TEST-0042 --to 2026-08-30T15:00
$ dealerhub-sandbox trigger test_drive.cancelled --lead L-TEST-0042
staging test chat: 3 messages, 3 different texts, each within 4 s of the trigger

$ curl -s -o /dev/null -w '%{http_code}\n' -X POST https://staging-bot.autodeal.example.com/webhooks/dealerhub \
    -H 'X-DealerHub-Signature: sha256=0000' -d @fixtures/confirmed.json
401

$ dealerhub-sandbox replay --event evt_test_7781
staging logs: "dealerhub webhook duplicate_event event_id=evt_test_7781", no message sent

$ npm test
Tests: 214 passed, 214 total
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | One message per event type | sandbox triggers, test chat | 3 messages | 3 messages | PASS |
| 2 | Bad signature rejected | curl with wrong signature | 401, no message | 401, no message | PASS |
| 3 | Replay ignored | sandbox replay | no second message | no message, duplicate logged | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Conversation behaviour | `npm test` | 214 passed |
| Other staging services | `docker service ls` before/after | unchanged |

## Not verified

- Real dealer tenants: subscriptions are registered by Adam with each dealer.

## Knowledge updated

- `knowledge/autodeal-bot/00-overview.md`: facts `webhook_signature`, `dealerhub_rate_limit`; trap about retries.

## Follow-ups

- none
