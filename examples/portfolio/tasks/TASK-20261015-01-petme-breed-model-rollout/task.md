---
id: TASK-20261015-01-petme-breed-model-rollout
title: Roll out breed model v3 to 10% of staging traffic
status: ready
tier: 1
product: petme
created: 2026-10-15
updated: 2026-10-16
owner: adam
---

# Roll out breed model v3 to 10% of staging traffic

## Goal

Breed model v3 serves 10% of breed-recognition requests on staging, with top-1 accuracy on live staging traffic no worse than v2 and p95 latency under 600 ms, so that a production canary can be decided on data.

Request: "v3 looks better offline. Let's see it on staging traffic first."

## Scope

Touch:
- `petme-vision` deployment config for staging (traffic split)
- `petme-api` feature flag `breed_model_v3_share` on staging

Do not touch:
- Production traffic split
- The training pipeline and the held-out set

Read only:
- Staging request logs and the labelled feedback table

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| Vision staging endpoint | service | `GET /info` → `env: staging` | to check at start |

## Plan

1. Confirm offline numbers: v3 top-1 0.87 vs v2 0.83 on the held-out set (tier 0).
2. Set `breed_model_v3_share=0.1` on staging (tier 1). Dry run: flag service `--dry-run` prints old and new value.
3. Collect 3 days of staging traffic with user feedback labels (tier 0).
4. Compare accuracy and latency per model.

## Rollback

- How: `breed_model_v3_share=0`.
- Tested: flag changes on staging are routine.
- Point of no return: none.

## Acceptance criteria

- [ ] 10% ± 2% of staging breed requests served by v3.
- [ ] v3 top-1 on labelled staging traffic ≥ v2's.
- [ ] v3 p95 latency < 600 ms.

## Verification

- Boundary checks: request logs by model version; feedback table join.
- Negative checks: mood recognition (separate model) latency and error rate unchanged.
- Watch afterwards: 3 days.

## Handoff

- State now: ready. Contract reviewed by Adam on 2026-10-16 ("looks good, start Monday").
- Last command and result: offline eval, v3 top-1 0.87.
- Next step: step 2 on 2026-10-19.

## Related tasks

- none
