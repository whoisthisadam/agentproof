---
id: TASK-20260914-02-shelfie-android-release-3-4-0
title: Shelfie Android 3.4.0 release
status: blocked
tier: 1
product: shelfie
created: 2026-09-14
updated: 2026-10-09
owner: adam
---

# Shelfie Android 3.4.0 release

## Goal

Shelfie 3.4.0 (OCR circuit breaker, warranty reminders redesign) is live for 100% of Android users with crash-free sessions at or above 99.5%.

Request: "Prepare 3.4.0 for Android. I'll do the upload."

## Scope

Touch:
- `shelfie` branch `release/3.4` (version bump, changelog)
- Firebase production functions deploy for 3.4.0 (`scanReceipt`, `processOcrQueue`): Tier 2, separate approval when the time comes

Do not touch:
- Signing keys and the Play Console (human-only: build upload and store listing)
- iOS release (separate task)

Read only:
- Crashlytics, Play Console vitals (screenshots from Adam)

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `shelfie@release/3.4` | repo | branch exists, CI green | yes |

## Plan

1. Version bump to 3.4.0 (versionCode 340012), changelog (tier 1).
2. `flutter build appbundle --flavor prod` on Adam's machine (signing key lives there) → verify manifest version (tier 0 for the agent).
3. **Human:** Adam uploads to the internal track, then 10% staged rollout.
4. Watch crash-free rate for 48 h, then Adam moves to 100%.

## Rollback

- How: halt the staged rollout in Play Console (human). Server side: functions are backward compatible with 3.3.
- Tested: n/a (store-side).
- Point of no return: 100% rollout (users can't be downgraded).

## Acceptance criteria

- [x] AAB has versionName 3.4.0, versionCode 340012.
- [ ] Internal track install works on two test devices.
- [ ] Crash-free sessions ≥ 99.5% at 10% for 48 h.

## Verification

- Boundary checks: `bundletool dump manifest`, test devices, Crashlytics.
- Negative checks: no change to signing config files in the diff.
- Watch afterwards: 48 h at 10%.

## Handoff

- State now: **blocked on a human-only step.** The AAB is built and verified (versionCode 340012) at `build/app/outputs/bundle/prodRelease/app-prod-release.aab` on Adam's machine. The upload to the internal track is Adam's.
- Last command and result: 2026-10-09 `bundletool dump manifest --bundle=... --xpath=/manifest/@android:versionCode` → `340012`.
- Next step: Adam uploads to the internal track and says so here; then the agent runs the test-device checks.
- Open questions: none. Smallest decision needed: "upload now or wait for the warranty copy fix?"

## Related tasks

- TASK-20260819-01-shelfie-ocr-timeout-followup
