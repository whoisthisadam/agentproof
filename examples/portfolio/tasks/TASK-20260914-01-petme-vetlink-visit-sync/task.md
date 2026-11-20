---
id: TASK-20260914-01-petme-vetlink-visit-sync
title: Import vet visit history from VetLink
status: in-progress
tier: 1
product: petme
created: 2026-09-14
updated: 2026-10-14
owner: adam
---

# Import vet visit history from VetLink

## Goal

A pet.me user who links their vet clinic's VetLink account sees their dog's past visits (date, reason, vaccinations) in the app within 5 minutes, and new visits within a day. Users currently type visits by hand, and it's the most requested feature.

Request: "VetLink finally gave us sandbox access. Let's pull visit history into the app."

## Scope

Touch:
- `petme-api/app/integrations/vetlink/**`, `petme-api/app/routes/vet_visits.py`
- Supabase **staging** project: new table `vet_visits` (migration), RLS policies
- `petme-app/src/screens/VetHistory/**`

Do not touch:
- Supabase production project
- VetLink production credentials (Adam requests them once the sandbox flow is accepted)

Read only:
- VetLink sandbox API and docs

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| Supabase staging | project | project ref ends in `stg`, name `petme-staging` | yes |
| VetLink sandbox | vendor | `GET /v1/whoami` → `partner: petme-sandbox` | yes |

## Plan

1. OAuth client-credentials flow and a typed client for `/patients` and `/visits` (tier 1).
2. Migration `0031_vet_visits.sql` with RLS: owners read their own dog's rows only (tier 1).
3. Initial import job on link; daily delta via `updated_since` (tier 1).
4. App screen (tier 1).
5. Test with the 12 sandbox patients, including pagination and the Sunday reset.

## Rollback

- How: revert the migration with `0031_vet_visits.down.sql` on staging; feature flag `vet_history` off in the app.
- Tested: down-migration tested on a local Supabase.
- Point of no return: none (staging only).

## Acceptance criteria

- [x] OAuth token obtained and refreshed before expiry.
- [x] All visits for the 12 sandbox patients imported, including patients with more than 50 visits (pagination).
- [ ] RLS: user A cannot read user B's visits (tested with two staging accounts).
- [ ] Daily delta picks up a visit added in the sandbox.
- [ ] App screen shows visits within 5 minutes of linking.

## Verification

- Boundary checks: staging API with two test accounts; app on a test device.
- Negative checks: existing tables' RLS policies unchanged (`supabase db diff`).
- Watch afterwards: none (staging).

## Handoff

- State now: client, migration and initial import work on staging (criteria 1–2). Pagination was the slow part: VetLink uses cursor pagination, not page numbers as its docs said; recorded in `knowledge/petme/00-overview.md`.
- Last command and result: 2026-10-14 `pytest tests/integrations/vetlink -k pagination` → 6 passed; import of sandbox patient `P-TEST-0007` (63 visits) complete.
- Next step: RLS test with two staging accounts (criterion 3). The accounts exist: `owner-a@example.com`, `owner-b@example.com`; their passwords are in the password manager under "pet.me staging test owners".
- Open questions: Does VetLink send vaccination batch numbers in production data? Sandbox has none. Asked VetLink support on 2026-10-13, no reply yet; not blocking.

## Related tasks

- none
