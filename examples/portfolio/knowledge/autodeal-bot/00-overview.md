---
last-verified: 2026-10-07
verified-by: TASK-20261006-01-autodeal-prompt-injection-hardening
verified-against: autodeal-bot@b81d3e0 (main)
---

# AutoDeal Bot: overview

## What it is

A Telegram and WhatsApp bot for used-car dealerships. It answers buyers' questions about cars in stock, qualifies the lead (budget, trade-in, financing), and books a test drive in the dealer's CRM. Four dealerships use it.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| Bot service | `autodeal-bot` | Node.js 20, TypeScript, grammY, WhatsApp Cloud API | Swarm stack `autodeal` on `swarm-mgr-01` |
| Conversation state | n/a | Redis 7 | `autodeal_redis`, AOF persistence |
| LLM | external | hosted LLM API | n/a |
| CRM integration | inside the bot | DealerHub CRM REST API + webhooks | n/a |

## Build and test

```bash
npm ci && npm test            # unit tests + recorded conversation fixtures
npm run eval                  # 120 scripted conversations, scores qualification accuracy
```

## Deploy

Tagged release → `docker service update --image … autodeal_bot` on `swarm-mgr-01` (Tier 2). Staging bot (`@autodeal_staging_bot`) on `build-runner-01`.

## Facts

```yaml
dealerhub_rate_limit: {value: "600 requests/min per dealer", how: reported, observed_at: 2026-08-26, source: "DealerHub CRM partner docs"}
eval_qualification_accuracy: {value: "0.91", how: measured, observed_at: 2026-10-07, source: TASK-20261006-01-autodeal-prompt-injection-hardening}
webhook_signature: {value: "HMAC-SHA256 over raw body, header X-DealerHub-Signature", how: measured, observed_at: 2026-08-27, source: TASK-20260826-01-autodeal-dealerhub-webhooks}
```

## Known traps

- Buyer messages are untrusted input to the LLM. Tool calls that write to the CRM need a confirmation step from the buyer and are limited to `create_lead` and `book_test_drive`. See [TASK-20261006-01-autodeal-prompt-injection-hardening](../../tasks/TASK-20261006-01-autodeal-prompt-injection-hardening/task.md).
- DealerHub retries webhooks for 24 hours with the same event ID. Handlers must be idempotent on `event_id`.
