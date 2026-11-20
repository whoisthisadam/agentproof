# Evidence: TASK-20260914-03-pulse-flaky-reminder-test

## Summary

`ReminderSchedulerIT.firesDueReminderOnce` failed in about 8% of runs on the CI runner. The scheduler's "due" query compared with PostgreSQL's `now()`, which is the **start time of the current transaction**, while the test computed the reminder time from the JVM clock a few dozen milliseconds later and truncated it to the second. Whenever a second boundary fell between the two, the reminder looked "not yet due". The fix takes "now" from the injected `Clock` and passes it into the query; the test uses a controllable clock and calls the scheduler directly. 200/200 repeated runs pass, a forced-failure experiment that failed 20/20 before now passes 20/20, and a real reminder fired exactly once on staging. Status: done.

## Commands and observations

Full journal: [journal.md](journal.md). Key steps:

**1. Reproduce (2026-09-14, on the CI runner)**

```text
$ agentproof fingerprint build-runner-01
OK build-runner-01: build-runner-01

$ ssh build-runner-01 'cd ~/ci/pulse-api && ./gradlew test --tests "app.pulse.reminders.ReminderSchedulerIT" -Pflaky.repeat=50'
ReminderSchedulerIT > firesDueReminderOnce() repetition 17 of 50 FAILED
    org.opentest4j.AssertionFailedError: expected: <1> but was: <0>
ReminderSchedulerIT > firesDueReminderOnce() repetition 38 of 50 FAILED
ReminderSchedulerIT > firesDueReminderOnce() repetition 41 of 50 FAILED
ReminderSchedulerIT > firesDueReminderOnce() repetition 44 of 50 FAILED
50 tests completed, 4 failed
```

4 of 50 (8%). On Adam's laptop the same command gave 0 of 50.

**2. Cause**

Code as of `pulse-api@9b31d07`:

```text
ReminderRepository.java:41   @Query("select r from Reminder r where r.fireAt <= now() and r.firedAt is null")
ReminderSchedulerIT.java:22  @Transactional                                   // whole test runs in one transaction
ReminderSchedulerIT.java:61  reminder.setFireAt(clock.instant().truncatedTo(SECONDS))   // clock = system UTC
ReminderSchedulerIT.java:64  scheduler.tick();
```

The transaction starts at time T0 (that's what `now()` returns for the rest of the test). The test then builds fixtures and computes `fireAt` at T1 = T0 + δ, truncated to the second. The reminder is due only if `trunc(T1) <= T0`. That fails exactly when a second boundary falls between T0 and T1, so the failure rate is roughly δ / 1 s. On the CI runner δ is about 80 ms (slower disk, container start-up in the same JVM) → about 8%. On the laptop δ is a few milliseconds → well under 1%, which is why it "never fails locally".

Confirmed by experiment rather than by reading: a temporary, uncommitted patch added `Thread.sleep(1100)` between the start of the transaction and the `fireAt` line, which guarantees a second boundary in between:

```text
$ ssh build-runner-01 'cd ~/ci/pulse-api && git apply ~/experiments/sleep-before-fireat.patch && ./gradlew test --tests "app.pulse.reminders.ReminderSchedulerIT" -Pflaky.repeat=20; git checkout -- .'
20 tests completed, 20 failed
    org.opentest4j.AssertionFailedError: expected: <1> but was: <0>
```

Deterministic failure with δ > 1 s: the transaction-time comparison is the cause.

Production impact: the scheduler runs each tick in its own short transaction, and the API and database run on the same host, so in production the effect is at most one extra poll interval (30 s) of delay. Not user-visible, but the scheduler's idea of "now" was implicit and untestable.

**3. Fix (branch `fix/reminder-clock`)**

```text
$ git diff --stat main...fix/reminder-clock
 src/main/java/app/pulse/reminders/ReminderRepository.java   |  4 ++--
 src/main/java/app/pulse/reminders/ReminderScheduler.java    |  6 +++---
 src/test/java/app/pulse/reminders/ReminderSchedulerIT.java  | 19 ++++++++++++-------
 src/test/java/app/pulse/support/MutableClock.java           | 31 +++++++++++++++++++++++++++++++
 4 files changed, 46 insertions(+), 14 deletions(-)
```

- `ReminderRepository.findDue(Instant now)`: `where r.fireAt <= :now and r.firedAt is null`.
- `ReminderScheduler.tick()` passes `clock.instant()`.
- The test uses `MutableClock`, disables the background trigger (`pulse.reminders.scheduler.enabled=false`) and calls `tick()` directly, so no second thread races the assertions.

**4. Verification on the runner**

```text
$ ssh build-runner-01 'cd ~/ci/pulse-api && git checkout -q fix/reminder-clock && ./gradlew test --tests "app.pulse.reminders.ReminderSchedulerIT" -Pflaky.repeat=200'
200 tests completed, 0 failed

$ ssh build-runner-01 'cd ~/ci/pulse-api && git apply ~/experiments/sleep-before-fireat.patch && ./gradlew test --tests "app.pulse.reminders.ReminderSchedulerIT" -Pflaky.repeat=20; git checkout -- src/test'
20 tests completed, 0 failed

$ ssh build-runner-01 'cd ~/ci/pulse-api && ./gradlew test'
412 tests completed, 0 failed, 3 skipped
BUILD SUCCESSFUL in 4m 6s
```

The experiment patch was applied to the test only and reverted after the run (`git status` clean, checked). The 3 skipped tests are the iOS push tests, skipped on CI by design.

**5. PR and merge**

PR "Reminder scheduler: take now from Clock, not from the database" merged 2026-09-15 10:31 UTC as `4f2a9c1`. CI for the merge commit: 412 passed, 0 failed, 3 skipped, 4m 11s. Staging deploy job finished 10:42 UTC.

**6. Staging**

```text
$ agentproof fingerprint build-runner-01
OK build-runner-01: build-runner-01

$ ssh build-runner-01 'docker service ls --format "{{.Name}} {{.Replicas}} {{.Image}}" | grep pulse_'
pulse_api 2/2 registry.example.com/pulse-api:2.14.1-4f2a9c1
pulse_db 1/1 postgres:16.4

$ curl -s -X POST https://staging-api.pulse.example.com/v1/reminders -H "Authorization: Bearer $PULSE_STAGING_TEST_TOKEN" \
    -d '{"medication":"test-vitamin-d","fireAt":"2026-09-15T10:50:00Z"}' | jq -r .id
rem_01J7ZT3Q8K

$ ssh build-runner-01 'docker service logs --since 10m pulse_api 2>&1 | grep rem_01J7ZT3Q8K'
pulse_api.1  2026-09-15T10:50:12Z INFO reminder.fired id=rem_01J7ZT3Q8K lagMs=12043 attempt=1
pulse_api.1  2026-09-15T10:50:12Z INFO push.sent reminder=rem_01J7ZT3Q8K platform=android status=accepted
```

Fired once, 12 s after its time (the scheduler polls every 30 s). `pulse_reminders_fired_total{env="staging"}` went up by exactly 1 between 10:49 and 10:52 UTC. The `docker service logs` fetch returned exit 0 and covered the full 10-minute window (first line 10:42:31, the deploy), so "only one `reminder.fired` line" is a real result, not a short read.

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Cause identified and shown by an experiment | sleep-before-fireAt patch, 20 repeats | fails every time before the fix | 20/20 failed before, 0/20 after | PASS |
| 2 | 200/200 repeated runs on `build-runner-01` | `-Pflaky.repeat=200` | 0 failed | 200 completed, 0 failed | PASS |
| 3 | Full suite passes on CI for the merge commit | CI run for `4f2a9c1` | 0 failed | 412 passed, 0 failed, 3 skipped | PASS |
| 4 | No retry mechanism added | `git diff main...fix/reminder-clock` searched for `Retry`, `retry`, `rerun` | no matches | no matches | PASS |
| 5 | Staging reminder fires once within 60 s | API create + logs + counter | 1 firing, lag < 60 s | 1 firing, lag 12 s, counter +1 | PASS |
| 6 | Knowledge states the rule | `knowledge/pulse/10-testing.md` | "Time comes from Clock" rule present | present, re-stamped | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Only files in *Scope → Touch* changed | `git diff --stat main...fix/reminder-clock` | 4 files, all under `reminders/` and `support/` |
| No migration added | `git diff --name-only main...fix/reminder-clock -- src/main/resources/db/migration` | empty |
| API contract | `OpenApiContractTest` in the full suite | passed, no diff |
| Experiment patch not left behind | `git status --porcelain` on the runner after each experiment | empty |
| Other staging services | `docker service ls` on `build-runner-01` at 10:20 and 10:45 | same 9 services, same replica counts; only `pulse_api` image changed |
| Production untouched | `ssh swarm-mgr-01 'docker service inspect pulse_api --format "{{.Spec.TaskTemplate.ContainerSpec.Image}}"'` (read only) | `pulse-api:2.14.0`, same as before |

## Not verified

- iOS push delivery: no test device is registered with the push sandbox, and the three iOS push tests are skipped on CI by design. The change doesn't touch push code.
- The production effect (at most one poll interval of delay) is reasoned from the code, not measured.

## Knowledge updated

- `knowledge/pulse/10-testing.md`: rule "Time comes from Clock", flaky-test verification rule, `known_flaky_tests` fact, trap about `now()` being transaction start time; re-stamped.
- `knowledge/pulse/00-overview.md`: known trap about time sources, `api_version_prod` fact; re-stamped.
- `inventory/hosts.yaml`: `build-runner-01` facts `os`, `timezone`, `private_ip` measured.

## Follow-ups

- none. The 7-day CI watch (31 runs on `main`, 0 failures, ended 2026-09-22) is recorded in the task's Handoff.
