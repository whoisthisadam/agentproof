---
id: TASK-20260914-03-pulse-flaky-reminder-test
title: Fix the flaky medication-reminder test in pulse-api
status: done
tier: 1
product: pulse
created: 2026-09-14
updated: 2026-09-15
owner: adam
---

# Fix the flaky medication-reminder test in pulse-api

## Goal

`ReminderSchedulerIT.firesDueReminderOnce` passes 200 times in a row on `build-runner-01`, the cause of the flakiness is known and fixed in production code if it's a real bug, and the fix is running on staging. It matters because CI on `main` has failed on this test about once a week for a month, and two releases were delayed by re-runs.

Request: "The reminder test is flaky again. Find out why and fix it properly, no retries."

## Scope

Touch:
- `pulse-api/src/main/java/app/pulse/reminders/**`
- `pulse-api/src/test/java/app/pulse/reminders/**`
- `pulse-api/src/test/java/app/pulse/support/**`
- Staging stack `pulse` on `build-runner-01` (deploy of the merged build)
- `knowledge/pulse/10-testing.md`, `knowledge/pulse/00-overview.md`

Do not touch:
- Test retries (`@RetryingTest`, Gradle `retry` plugin). The request says no retries.
- Database migrations in `src/main/resources/db/migration`.
- Production stack on `swarm-mgr-01`. The production release is a separate task.
- Other flaky-looking tests found along the way: note them as follow-ups.

Read only:
- CI history on `build-runner-01` (`/var/lib/ci/logs/pulse-api/`)
- Grafana dashboard "Pulse API" (staging)

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `pulse-api@main` | repo | branch `main`, clean working tree | yes, 2026-09-14 |
| `build-runner-01` | host (lab) | `cat /etc/agentproof/host-id` = `build-runner-01` | yes, 2026-09-14 and 2026-09-15 |
| staging `pulse` stack | Swarm stack | `docker stack ls` on `build-runner-01` lists `pulse` | yes, 2026-09-15 |

## Plan

1. Reproduce (tier 0): run the test 50 times on `build-runner-01`; record the failure rate and the failure message.
2. Find the cause (tier 0): read the test and the scheduler; compare time sources; confirm with a targeted experiment (a temporary, uncommitted patch on the runner, reverted after each run).
3. Fix (tier 1): smallest change on branch `fix/reminder-clock` that removes the cause. Dry run: `git diff --stat` reviewed against *Scope → Touch* before commit.
4. Verify locally on the runner (tier 0): 200 repeated runs of the test, then the full suite.
5. Open a PR, wait for CI, merge to `main` (tier 1). The merge deploys to staging automatically.
6. Verify on staging (tier 1): create a reminder for the test user one minute ahead; confirm exactly one `reminder.fired` event and one push attempt.
7. Update `knowledge/pulse/10-testing.md` and re-stamp `00-overview.md`.

## Rollback

- How: `git revert <merge-commit>` on `main`; CI redeploys staging. For staging only and immediately: [RB-01](../../runbooks/RB-01-swarm-service-rollback.md) on `build-runner-01`, service `pulse_api`.
- Tested: the RB-01 path was used on `build-runner-01` on 2026-09-10 (TASK-20260909-01-pulse-postgres-16-migration). Revert not tested; it's a code-only change with no migration.
- Point of no return: none. No schema or data change.

## Acceptance criteria

- [x] The cause is identified and shown by an experiment, not only by reading code.
- [x] `ReminderSchedulerIT` passes 200 out of 200 repeated runs on `build-runner-01`.
- [x] The full test suite passes on CI for the merge commit.
- [x] No test retry mechanism added.
- [x] Staging: one reminder created one minute ahead fires exactly once, within 60 s of its time.
- [x] `knowledge/pulse/10-testing.md` states the rule that prevents this class of bug.

## Verification

- Boundary checks: repeated test runs on `build-runner-01` (the CI runner, where it flakes); CI result for the merge commit; staging API + `reminder.fired` log line + push attempt metric.
- Negative checks: `git diff --stat` contains only files under *Scope → Touch*; no new migration file; OpenAPI contract test unchanged; other services in the staging stack keep their replica counts and images; production `pulse_api` image unchanged.
- Watch afterwards: CI on `main` for 7 days (any failure of `ReminderSchedulerIT` reopens this as a new task).

## Approvals

Not required (tier 1). Adam confirmed the plan in chat on 2026-09-14: "plan ok, go".

## Handoff

- State now: done. Fix merged as `4f2a9c1`, running on staging since 2026-09-15 10:42 UTC.
- Last command and result: 7-day CI watch ended 2026-09-22: 31 runs on `main`, 0 failures of `ReminderSchedulerIT`.
- Next step: none. Production gets the fix with the next release.
- Open questions: none.

## Related tasks

- TASK-20260909-01-pulse-postgres-16-migration (same service, earlier RB-01 use)
