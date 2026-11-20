---
id: TASK-20260826-01-autodeal-dealerhub-webhooks
title: Receive DealerHub CRM webhooks for test-drive status changes
status: done
tier: 1
product: autodeal-bot
created: 2026-08-26
updated: 2026-08-28
owner: adam
---

# Receive DealerHub CRM webhooks for test-drive status changes

## Goal

When a dealer confirms, moves or cancels a test drive in DealerHub CRM, the buyer gets a message from the bot within a minute. Today buyers hear nothing until the dealer calls them, and two dealers asked for this.

Request: "Dealers want the bot to tell buyers when they confirm or move a test drive in DealerHub."

## Scope

Touch:
- `autodeal-bot/src/integrations/dealerhub/**`, `autodeal-bot/src/routes/webhooks.ts`
- Staging stack `autodeal` on `build-runner-01`
- DealerHub **sandbox** webhook subscription

Do not touch:
- DealerHub production subscriptions (registered by Adam with each dealer)
- Production stack on `swarm-mgr-01`

Read only:
- DealerHub partner docs and sandbox

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `build-runner-01` | host | host-id = `build-runner-01` | yes |
| DealerHub sandbox | vendor | tenant `sandbox-autodeal` | yes |

## Plan

1. Endpoint `POST /webhooks/dealerhub` with HMAC-SHA256 verification over the raw body (tier 1).
2. Idempotency on `event_id` in Redis (24 h, matching DealerHub's retry window) (tier 1).
3. Deploy to staging, subscribe the sandbox tenant, trigger each event type (tier 1).

## Rollback

- How: RB-01 on `build-runner-01` for `autodeal_bot`; delete the sandbox subscription.
- Tested: yes (RB-01 is routine on staging).
- Point of no return: none.

## Acceptance criteria

- [x] Confirmed, rescheduled and cancelled events each produce one buyer message on the staging bot.
- [x] A request with a bad signature gets 401 and no message.
- [x] A replayed event (same `event_id`) produces no second message.

## Verification

- Boundary checks: sandbox-triggered events and the staging Telegram test chat.
- Negative checks: existing bot conversation tests (`npm test`) green; other staging services unchanged.
- Watch afterwards: none.

## Handoff

- State now: done.
- Last command and result: 2026-08-28, replay test: 1 message, 1 `duplicate_event` log line.
- Next step: none.

## Related tasks

- TASK-20261006-01-autodeal-prompt-injection-hardening
