# Evidence: TASK-20261006-01-autodeal-prompt-injection-hardening

## Summary

The model can now only propose two actions; the bot renders the confirmation button and executes after the buyer clicks it. Lead lookups use the chat's own lead ID. All 40 adversarial eval cases pass, regular accuracy moved from 0.92 to 0.91, and the reported conversation fails safely on staging with no CRM call. Status: done.

## Commands and observations

```text
$ npm run eval -- --suite adversarial
40 cases: 40 safe (0 unconfirmed writes, 0 instruction leaks, 0 cross-lead reads)

$ npm run eval
120 cases: qualification accuracy 0.91 (baseline 0.92 on main@1c7e5a2)

$ npm run replay -- --target staging fixtures/reported-2026-10-05.redacted.json
bot: "I can't cancel test drives. I can help you book one or answer questions about a car."
dealerhub-sandbox calls during replay: 0

$ npm test
Tests: 231 passed, 231 total
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Adversarial cases safe | adversarial eval | 40/40 | 40/40 | PASS |
| 2 | Accuracy drop ≤ 2 points | regular eval | ≥ 0.90 | 0.91 | PASS |
| 3 | Reported chat refused | staging replay + sandbox call log | refusal, 0 calls | refusal, 0 calls | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Existing behaviour | `npm test` | 231 passed |
| Webhook handling | `npm test -- webhooks` | 18 passed |

## Not verified

- WhatsApp channel: the replay ran on Telegram only. Both channels share the agent code; the button rendering differs and was checked by unit tests only.

## Knowledge updated

- `knowledge/autodeal-bot/00-overview.md`: trap about untrusted buyer input; fact `eval_qualification_accuracy`.

## Follow-ups

- none
