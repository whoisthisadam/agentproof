# Evidence: TASK-20260909-01-pulse-postgres-16-migration

## Summary

Pulse production moved from PostgreSQL 14.12 to 16.4 by dump and restore into a new volume. Downtime was 19 minutes. Row counts of all 23 tables match; smoke tests and the 24 h watch were clean. The old volume is kept until 2026-09-23. Status: done.

## Commands and observations

```text
# Rehearsal on build-runner-01 (2026-09-09 15:10 UTC)
pg_restore: 23 tables, 0 errors; ./gradlew test -Pdb=lab16 -> 409 passed, 0 failed
switch back to 14 tested: 40 s

# Window (times local, 2026-09-09)
23:01 docker service scale pulse_api=0             -> converged
23:02 pg_dump -Fc pulse > /srv/backup/pulse-20260909.dump ; sha256sum -> recorded in artifacts (not committed)
23:09 postgres:16.4 on pulse_pgdata16 ; pg_restore -j 4 -> 0 errors
23:14 row counts: 23/23 tables match (users 3,214; lab_results 48,902; reminders 61,377; ...)
23:16 ANALYZE
23:18 docker service update --mount-rm ... --mount-add source=pulse_pgdata16 ... --image postgres:16.4 pulse_db
23:20 docker service scale pulse_api=2             -> 2/2 running

$ curl -s -o /dev/null -w '%{http_code}\n' https://api.pulse.example.com/health
200
$ ./scripts/smoke.sh production
login ok, lab results ok (12 items), reminder create+delete ok
$ psql -c 'select version()'
PostgreSQL 16.4 on x86_64-pc-linux-gnu
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Version 16.4 | `select version()` | 16.4 | 16.4 | PASS |
| 2 | Row counts match | count script, 23 tables | all equal | 23/23 equal | PASS |
| 3 | API healthy, smoke tests pass | health + smoke | 200, all ok | 200, all ok | PASS |
| 4 | Downtime < 30 min | scale-down to scale-up | < 30 min | 19 min | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Other stacks | `docker service ls` before/after | same services, replicas, images |
| Old volume | `docker volume inspect pulse_pgdata` | exists, not mounted, size unchanged |

## Not verified

- iOS push after the switch: no sandbox device (standing gap, see Pulse overview).

## Knowledge updated

- `knowledge/pulse/00-overview.md`: fact `postgres_version`.
- `runbooks/RB-01-swarm-service-rollback.md`: precondition about migrations.
- `inventory/hosts.yaml`: `swarm-mgr-01` facts.

## Follow-ups

- none (old volume deletion is a dated human step in Handoff)
