# Evidence: TASK-20260811-01-rentradar-kafka-retention

## Summary

`listings.raw` retention changed from 7 days to 72 hours after confirming the slowest consumer group was 3 minutes behind. Old segments were deleted within minutes; the volume went from 74% to 41% in 24 hours. Status: done.

## Commands and observations

```text
$ ssh swarm-mgr-01 'docker exec $(docker ps -q -f name=rentradar_kafka) kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --all-groups' | awk '{print $1, $2, $6}' | sort -u
rr-matcher listings.raw 112
rr-archiver listings.raw 0
(max lag 112 messages, about 3 minutes)

$ ssh swarm-mgr-01 'docker exec ... kafka-configs.sh --bootstrap-server 127.0.0.1:9092 --alter --entity-type topics --entity-name listings.raw --add-config retention.ms=259200000'
Completed updating config for topic listings.raw.

$ ssh swarm-mgr-01 'df -h /var/lib/docker/volumes/rentradar_kafka/_data | tail -1'
2026-08-11 10:05  /dev/sdb1  200G  148G  52G  74%
2026-08-12 10:10  /dev/sdb1  200G   82G 118G  41%
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | retention.ms set | `kafka-configs.sh --describe` | 259200000 | 259200000 | PASS |
| 2 | No consumer needs older data | consumer group lag | < 72 h | max 3 min | PASS |
| 3 | Disk below 50% in 24 h | `df` | < 50% | 41% | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Other topics | `--describe` on `listings.normalised`, `alerts.outbound` | unchanged (7 d, 3 d) |
| Alerts delivered | `alerts.outbound` message rate, day before vs day after | 1,940 vs 2,012 |

## Not verified

- Nothing.

## Knowledge updated

- `knowledge/rentradar/00-overview.md`: fact `listings_raw_retention`.

## Follow-ups

- none
