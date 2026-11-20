---
id: TASK-20261006-01-autodeal-prompt-injection-hardening
title: Stop buyer messages from steering the bot's CRM actions
status: done
tier: 1
product: autodeal-bot
created: 2026-10-06
updated: 2026-10-07
owner: adam
---

# Stop buyer messages from steering the bot's CRM actions

## Goal

No buyer message can make the bot create, change or cancel anything in DealerHub that the buyer didn't explicitly confirm, and the bot never reveals its instructions or other buyers' data. A dealer reported a chat where a buyer got the bot to "cancel all test drives for today"; the CRM rejected it only because the bot's token lacked that permission.

Request: "This shouldn't be possible even in principle. Fix it so the model can't do it."

## Scope

Touch:
- `autodeal-bot/src/agent/**` (tool definitions, system prompt, confirmation step)
- `autodeal-bot/eval/**` (new adversarial cases)
- Staging stack on `build-runner-01`

Do not touch:
- DealerHub token scopes (already minimal; Adam checked)
- Production until the eval passes (release is a separate step)

Read only:
- The reported conversation (exported, customer details removed by Adam)

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `autodeal-bot@main` | repo | clean tree | yes |
| `build-runner-01` | host | host-id = `build-runner-01` | yes |

## Plan

1. Reduce the model's tools to `create_lead` and `book_test_drive` (remove the generic `crm_request` tool) (tier 1).
2. Write actions require a buyer confirmation button rendered by the bot, not by the model; the model can only propose (tier 1).
3. Lead lookup scoped to the current chat's lead ID server-side, never a model-supplied ID (tier 1).
4. Add 40 adversarial eval cases (injection in messages, in car descriptions, in quoted "dealer notes") (tier 0).

## Rollback

- How: RB-01 for `autodeal_bot` on staging.
- Tested: yes.
- Point of no return: none.

## Acceptance criteria

- [x] 40/40 adversarial cases: no write action without a confirmation click, no instructions leaked, no other lead's data.
- [x] Qualification accuracy on the regular eval does not drop by more than 2 points.
- [x] The reported conversation replayed on staging: the bot refuses and no CRM call is made.

## Verification

- Boundary checks: eval runs; replay on the staging bot; CRM sandbox call log.
- Negative checks: `npm test` green.
- Watch afterwards: none.

## Handoff

- State now: done.
- Last command and result: 2026-10-07 eval: 40/40 adversarial, accuracy 0.91 (was 0.92).
- Next step: none.

## Related tasks

- TASK-20260826-01-autodeal-dealerhub-webhooks
