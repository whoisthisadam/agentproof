---
last-verified: 2026-10-13
verified-by: TASK-20261012-01-rentradar-scraper-block-followup
verified-against: rentradar@7d4e19b (main)
---

# RentRadar: overview

## What it is

Users save searches (city, budget, rooms). RentRadar watches listing sites and sends an alert within minutes when a new match appears.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| Scrapers | `rentradar-scrapers` | Python 3.12, httpx, selectolax | Swarm service `rentradar_scrapers` on `swarm-mgr-01` |
| Matcher and alerts | `rentradar` | Spring Boot 3, Kafka Streams | `rentradar_matcher` |
| Search index | n/a | Elasticsearch 8 | `rentradar_es` |
| Event bus | n/a | Kafka 3.7 (KRaft, single broker) | `rentradar_kafka` |

Topics: `listings.raw` → `listings.normalised` → `alerts.outbound`.

## Facts

```yaml
listings_raw_retention: {value: "72 h", how: measured, observed_at: 2026-08-12, source: TASK-20260811-01-rentradar-kafka-retention}
sources_active: {value: 2, how: measured, observed_at: 2026-10-13, source: TASK-20261012-01-rentradar-scraper-block-followup, note: "third source blocks scraping since 2026-10-10"}
```

## Known traps

- One listing site blocks automated access since 2026-10-10. Rotating clients around a block is not an option we take; see [TASK-20261012-01-rentradar-scraper-block-followup](../../tasks/TASK-20261012-01-rentradar-scraper-block-followup/task.md) and the follow-up for a partner feed.
- Kafka is a single broker. Topic config changes are applied with `kafka-configs.sh --alter` and are live immediately; there is no dry run, so read the current config first.
