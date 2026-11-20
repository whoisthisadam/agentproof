---
last-verified: 2026-09-15
verified-by: TASK-20260914-03-pulse-flaky-reminder-test
verified-against: pulse-api@4f2a9c1 (main)
---

# Pulse: overview

## What it is

A personal health tracker. People store lab results, keep a calendar of doctor visits and get medication reminders as push notifications. About 3,000 monthly active users, mostly on Android.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| API | `pulse-api` | Spring Boot 3.3, Java 21, Flyway | Swarm stack `pulse` on `swarm-mgr-01` (prod), `build-runner-01` (staging) |
| Database | n/a | PostgreSQL 16 | `pulse_db` service, volume `pulse_pgdata`, nightly dump to object storage |
| Android | `pulse-android` | Kotlin, Jetpack Compose | Play Store |
| iOS | `pulse-ios` | Swift, SwiftUI | App Store |
| Reminder scheduler | inside `pulse-api` | Spring `@Scheduled`, every 30 s | same as API |

## Build and test

```bash
./gradlew test                 # unit + Testcontainers integration tests (needs Docker)
./gradlew bootJar              # builds build/libs/pulse-api.jar
docker build -t registry.example.com/pulse-api:<version> .
```

CI runs on `build-runner-01`. The full test suite takes about 4 minutes.

## Deploy

- **Staging:** every merge to `main` deploys to the staging stack on `build-runner-01` (`docker stack deploy -c deploy/staging.yml pulse`). Tier 1.
- **Production:** tagged release, `docker service update --image … --update-failure-action rollback pulse_api` on `swarm-mgr-01`. Tier 2. Rollback: [RB-01](../../runbooks/RB-01-swarm-service-rollback.md).

## Environments

| Environment | URL | Hosts |
|---|---|---|
| staging | `https://staging-api.pulse.example.com` | `build-runner-01` |
| production | `https://api.pulse.example.com` | `swarm-mgr-01` |

## Facts

```yaml
postgres_version: {value: "16.4", how: measured, observed_at: 2026-09-10, source: TASK-20260909-01-pulse-postgres-16-migration}
api_version_prod: {value: "2.14.0", how: measured, observed_at: 2026-09-15, source: TASK-20260914-03-pulse-flaky-reminder-test}
reminder_poll_interval: {value: "30 s", how: measured, observed_at: 2026-09-14, source: "pulse-api@4f2a9c1 application.yml"}
```

## Known traps

- Time in the scheduler and in tests comes from the injected `Clock`, never from the database's `now()`. See [10-testing.md](10-testing.md).
- Push notifications on iOS can't be tested on staging (no test device registered with the sandbox). Every release task lists this under *Not verified*.
