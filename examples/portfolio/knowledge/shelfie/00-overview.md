---
last-verified: 2026-10-09
verified-by: TASK-20260914-02-shelfie-android-release-3-4-0
verified-against: shelfie@a6f9022 (release/3.4)
---

# Shelfie: overview

## What it is

A home inventory app. Snap a receipt, Shelfie reads it, and tracks warranties and expiry dates for what you bought.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| App | `shelfie` | Flutter 3.24 (Android, iOS) | stores |
| Backend | `shelfie` (`functions/`) | Firebase Auth, Firestore, Cloud Functions (TypeScript) | Firebase project `shelfie-prod` |
| OCR | external | ReceiptLens OCR API | n/a |

## Build and release

```bash
flutter test
flutter build appbundle --flavor prod      # Android
flutter build ipa --flavor prod            # iOS
```

Store uploads and signing are **human-only**. The agent builds and verifies the artifact, then hands over.

## Facts

```yaml
receiptlens_p95_latency: {value: "2.8 s", how: measured, observed_at: 2026-08-21, source: TASK-20260819-01-shelfie-ocr-timeout-followup}
ocr_client_timeout: {value: "8 s, 1 retry, circuit opens after 5 failures in 60 s", how: measured, observed_at: 2026-08-21, source: TASK-20260819-01-shelfie-ocr-timeout-followup}
android_version_code_3_4_0: {value: 340012, how: measured, observed_at: 2026-10-09, source: TASK-20260914-02-shelfie-android-release-3-4-0}
```

## Known traps

- Release builds need the upload key, which only exists on Adam's machine. Agents never create or import signing material.
