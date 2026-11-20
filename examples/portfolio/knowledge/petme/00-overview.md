---
last-verified: 2026-10-14
verified-by: TASK-20260914-01-petme-vetlink-visit-sync
verified-against: petme-api@93c0e7a (main)
---

# pet.me: overview

## What it is

An app for dog owners: feeding plans by breed, age and weight, a behaviour Q&A assistant, vet visit history, and breed and mood recognition from photos.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| App | `petme-app` | React Native (Expo) | App Store, Play Store |
| API | `petme-api` | Python 3.12, FastAPI | managed container platform, region eu-west |
| Auth, DB, storage | n/a | Supabase (Postgres, Auth, Storage) | managed |
| Vision | `petme-vision` | fine-tuned image classifier behind an internal endpoint | GPU instance, managed |
| Vet records | external | VetLink API (OAuth 2.0 client credentials) | n/a |

## Build and test

```bash
uv sync && uv run pytest            # API
npm ci && npx jest                  # app
uv run python -m petme_vision.eval  # breed top-1 accuracy on the held-out set
```

## Facts

```yaml
breed_model_top1: {value: "0.87", how: measured, observed_at: 2026-10-15, source: TASK-20261015-01-petme-breed-model-rollout}
vetlink_sandbox_rate_limit: {value: "60 requests/min", how: reported, observed_at: 2026-09-14, source: "VetLink sandbox docs"}
vetlink_visit_pagination: {value: "cursor-based, 50 per page", how: measured, observed_at: 2026-10-14, source: TASK-20260914-01-petme-vetlink-visit-sync}
```

## Known traps

- VetLink sandbox data is reset every Sunday at 00:00 UTC. Integration tests that rely on sandbox records fail on Sunday mornings.
- Photos may contain people. The vision pipeline crops to the dog before storage; never log raw images.
