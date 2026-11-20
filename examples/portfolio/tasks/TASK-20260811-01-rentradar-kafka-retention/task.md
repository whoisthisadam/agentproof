---
id: TASK-20260811-01-rentradar-kafka-retention
title: Cut retention of listings.raw from 7 days to 72 hours
status: done
tier: 1
product: rentradar
created: 2026-08-11
updated: 2026-08-12
owner: adam
---

# Cut retention of listings.raw from 7 days to 72 hours

## Goal

Topic `listings.raw` keeps 72 hours of data instead of 7 days, so the Kafka volume on `swarm-mgr-01` stops growing toward its 80% disk alert (it was at 74%). Nothing downstream reads raw listings older than 24 hours.

Request: "Kafka disk alert is going to fire this week. Can we keep less raw data?"

## Scope

Touch:
- Topic config `retention.ms` of `listings.raw` only

Do not touch:
- `listings.normalised`, `alerts.outbound`
- Broker-level defaults, the Kafka service, the volume

Read only:
- `swarm-mgr-01` (consumer group lag, disk usage)

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `swarm-mgr-01` | host | `cat /etc/agentproof/host-id` = `swarm-mgr-01` | yes |
| Kafka cluster | service | `kafka-cluster.sh cluster-id` = `rr-kafka-prod` | yes |

## Plan

1. Read current topic config and the oldest offset each consumer group still needs (tier 0).
2. `kafka-configs.sh --alter --entity-type topics --entity-name listings.raw --add-config retention.ms=259200000` (tier 1; Kafka has no dry run, so step 1 is the substitute).
3. Watch log segment deletion and disk usage for 24 h.

## Rollback

- How: same command with `retention.ms=604800000`. Data already deleted is not recoverable, which is why step 1 checks consumer lag first.
- Tested: no.
- Point of no return: the first segment deletion (within 5 minutes of the change).

## Acceptance criteria

- [x] `retention.ms` of `listings.raw` is 259200000.
- [x] No consumer group lags more than 72 h behind.
- [x] Kafka volume usage drops below 50% within 24 h.

## Verification

- Boundary checks: `kafka-configs.sh --describe`, `df` on the volume, consumer lag.
- Negative checks: config of the other two topics unchanged.
- Watch afterwards: 24 h.

## Handoff

- State now: done.
- Last command and result: 2026-08-12, volume at 41%.
- Next step: none.

## Related tasks

- none
