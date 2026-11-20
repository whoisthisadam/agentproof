# Example portfolio

A complete, **fictional** workspace of a solo developer running six products with AI agents under agentproof. Everything here is made up: products, vendors, people, domains (`example.com`) and IPs (documentation ranges).

Use it to see what the protocol looks like after a few months of real use, and as a test fixture: CI runs `agentproof --root examples/portfolio validate` on it.

## Start here

1. [tasks/README.md](tasks/README.md): the generated ledger. What's open, what's done.
2. **The worked example:** [TASK-20260914-03-pulse-flaky-reminder-test](tasks/TASK-20260914-03-pulse-flaky-reminder-test/task.md). A flaky test followed from request to root cause, fix, staging deploy, evidence and knowledge update. Every file is filled in.
3. **The infrastructure example:** [TASK-20260921-01-tunnelr-add-node-toronto](tasks/TASK-20260921-01-tunnelr-add-node-toronto/task.md). A Tier 2 production change over SSH: approval, fingerprint, dry run, point of no return, rollback.
4. Then browse: a [failed task](tasks/TASK-20261012-01-rentradar-scraper-block-followup/task.md) with its follow-up, a [blocked release](tasks/TASK-20260914-02-shelfie-android-release-3-4-0/task.md) waiting on a human-only step, an [in-progress integration](tasks/TASK-20260914-01-petme-vetlink-visit-sync/task.md) with its handoff.

## The products

| Product | What it is | Stack |
|---|---|---|
| [Pulse](knowledge/pulse/00-overview.md) | Personal health tracker: lab results, doctor visits, medication reminders | Kotlin (Android), Swift (iOS), Spring Boot API, PostgreSQL |
| [AutoDeal Bot](knowledge/autodeal-bot/00-overview.md) | Telegram/WhatsApp bot that qualifies leads for used-car dealerships and books test drives | Node.js/TypeScript, LLM API, Redis, dealer CRM webhooks |
| [pet.me](knowledge/petme/00-overview.md) | AI app for your dog: feeding plans, behaviour Q&A, vet history, breed and mood from photos | React Native, Python FastAPI, vision model, Supabase |
| [Tunnelr](knowledge/tunnelr/00-overview.md) | Consumer VPN with WireGuard exit nodes in several regions | Go, WireGuard, Docker Swarm, Terraform, Grafana/Prometheus |
| [RentRadar](knowledge/rentradar/00-overview.md) | Watches rental listings and alerts on new matches | Python scrapers, Spring Boot, Kafka, Elasticsearch |
| [Shelfie](knowledge/shelfie/00-overview.md) | Home inventory: scan receipts, track warranties and expiry dates | Flutter, OCR service, Firebase |

## Layout

```text
knowledge/    how each product works today (stamped)
inventory/    hosts.yaml: three machines, identity only
runbooks/     approved procedures
decisions/    ADRs
tasks/        thirteen tasks across the products, plus the generated ledger
.env.example  variable names the products use
```
