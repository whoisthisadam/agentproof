---
last-verified: 2026-09-15
verified-by: TASK-20260914-03-pulse-flaky-reminder-test
verified-against: pulse-api@4f2a9c1 (main)
---

# Pulse: testing

## Layout

| Suite | Path | Notes |
|---|---|---|
| Unit | `src/test/java/.../unit` | no Spring context, runs in seconds |
| Integration | `src/test/java/.../it` | Spring Boot + Testcontainers PostgreSQL 16 |
| Contract | `src/test/resources/openapi` | `openapi.yaml` diffed against the generated spec |

## Rules

- **Time comes from `Clock`.** Production code takes a `java.time.Clock` bean. Repository queries that compare with "now" take it as a parameter (`findDue(Instant now)`), never `now()` in SQL. Tests use `Clock.fixed(...)` or `MutableClock`. Since [TASK-20260914-03-pulse-flaky-reminder-test](../../tasks/TASK-20260914-03-pulse-flaky-reminder-test/task.md).
- **Flaky means rerun 50 times before and after.** A fix for a flaky test is only verified with a repeated run: `./gradlew test --tests '<name>' -Pflaky.repeat=50`. The property is wired to JUnit's `@RepeatedTest` via a custom extension in `src/test/java/.../support/RepeatExtension.java`.
- **One Testcontainers database per test class**, reset with Flyway `clean` + `migrate` in `@BeforeAll`. Never share state between classes.

## Facts

```yaml
suite_duration: {value: "about 4 min on build-runner-01", how: measured, observed_at: 2026-09-15, source: TASK-20260914-03-pulse-flaky-reminder-test}
known_flaky_tests: {value: [], how: measured, observed_at: 2026-09-15, source: TASK-20260914-03-pulse-flaky-reminder-test, note: "200 repeated runs, 0 failures"}
```

## Known traps

- In PostgreSQL, `now()` is the start time of the current transaction, not the current time. A test that runs inside one transaction and compares with `now()` sees a frozen clock.
- The CI runner is slower than a laptop, so timing gaps inside a test are larger there. A test that "never fails locally" and fails a few percent of the time in CI is usually a time-source or ordering bug, not CI noise.
