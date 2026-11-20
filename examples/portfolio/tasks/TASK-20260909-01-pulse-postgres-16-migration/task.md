---
id: TASK-20260909-01-pulse-postgres-16-migration
title: Upgrade Pulse production database from PostgreSQL 14 to 16
status: done
tier: 2
product: pulse
created: 2026-09-09
updated: 2026-09-10
owner: adam
---

# Upgrade Pulse production database from PostgreSQL 14 to 16

## Goal

Pulse production runs on PostgreSQL 16.4 with all data intact and the API healthy. PostgreSQL 14 support ends within the year, and the API upgrade planned next needs 15+.

Request: "Let's get Pulse onto Postgres 16 this week, Wednesday night is fine for downtime."

## Scope

Touch:
- Service `pulse_db` and volume `pulse_pgdata` on `swarm-mgr-01` (new volume `pulse_pgdata16`)
- `pulse_api` (scaled to 0 and back for the window)
- `deploy/production.yml` in `pulse-api` (image tag and volume name)

Do not touch:
- Any other stack on `swarm-mgr-01`
- The old volume `pulse_pgdata`: kept for 14 days as the rollback

Read only:
- Nightly dump bucket

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `swarm-mgr-01` | host | host-id = `swarm-mgr-01` | yes, before and after |
| Pulse DB | database | `SELECT current_database()` = `pulse` and row count of `users` matches pre-check | yes |

## Plan

1. Rehearse on `build-runner-01` with last night's dump: `pg_dump` 14 → `pg_restore` into 16, run the API test suite against it (tier 1).
2. Window, Wed 2026-09-09 23:00 local: announce in-app banner (done the day before).
3. Scale `pulse_api` to 0; final `pg_dump -Fc` from 14 to the host; checksum (tier 2).
4. Start `postgres:16.4` on new volume `pulse_pgdata16`; `pg_restore` (tier 2).
5. Compare row counts of all 23 tables; run `ANALYZE` (tier 1).
6. Point `pulse_db` at the new volume; scale `pulse_api` back to 2 (tier 2).

## Rollback

- How: point `pulse_db` back at `pulse_pgdata` with `postgres:14` and scale the API up. The old volume is untouched by the plan.
- Tested: yes, on `build-runner-01` during the rehearsal (switch back took 40 s).
- Point of no return: the first write by the API to the new database (step 6). After it, rolling back loses those writes; a forward fix is preferred.

## Acceptance criteria

- [x] `SELECT version()` reports 16.4.
- [x] Row counts of all 23 tables match the dump.
- [x] API health 200 and the smoke test suite passes against production.
- [x] Downtime under 30 minutes.

## Verification

- Boundary checks: API health, smoke tests (login, list lab results, create reminder), app on a test device.
- Negative checks: other stacks on `swarm-mgr-01` unchanged; old volume untouched.
- Watch afterwards: error rate and slow-query log for 24 h.

## Approvals

- Approved by: Adam
- When: 2026-09-09 18:20 UTC
- Exact scope: steps 3–6 on `swarm-mgr-01` for the Pulse stack only, in tonight's window; keep the old volume 14 days
- Their words: "approved for tonight, steps 3-6, keep the old volume"

## Handoff

- State now: done.
- Last command and result: 2026-09-10 23:30 local, 24 h watch: no errors above baseline.
- Next step: delete old volume `pulse_pgdata` after 2026-09-23 (human-only: data deletion).

## Related tasks

- TASK-20260914-03-pulse-flaky-reminder-test
