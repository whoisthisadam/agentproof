---
id: TASK-20261012-01-rentradar-scraper-block-followup
title: Restore listings from the third source after it started blocking the scraper
status: failed
tier: 1
product: rentradar
created: 2026-10-12
updated: 2026-10-13
owner: adam
---

# Restore listings from the third source after it started blocking the scraper

## Goal

New listings from the third listing site reach RentRadar alerts again. Since 2026-10-10 every request from the scraper gets HTTP 403 with a bot-check page, and alerts for that city dropped by about 40%.

Request: "Source 3 is returning 403s since Friday. See if you can get it working again."

## Scope

Touch:
- `rentradar-scrapers/sources/source3/**`
- Staging scraper service on `build-runner-01`

Do not touch:
- Anything that evades the site's bot protection: rotating IPs or proxies, faking browser fingerprints, solving challenges. If the site doesn't want automated access, we stop.
- Production scraper config on `swarm-mgr-01`

Read only:
- The site's robots.txt and terms of use
- Scraper logs

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| `build-runner-01` | host | host-id = `build-runner-01` | yes |

## Plan

1. Read logs, robots.txt and terms (tier 0).
2. If the block is a misconfiguration on our side (rate, missing header, outdated endpoint), fix it (tier 1).
3. If the site has decided to block automated access, stop and propose a partner feed.

## Rollback

- How: revert the scraper change; redeploy staging.
- Tested: n/a, nothing deployed.
- Point of no return: none.

## Acceptance criteria

- [ ] Source 3 returns listings to the staging scraper without evading any protection.

## Verification

- Boundary checks: staging scraper run, listing count.
- Negative checks: sources 1 and 2 unaffected.
- Watch afterwards: none.

## Handoff

- State now: failed. The site changed its terms and robots.txt on 2026-10-10 to disallow automated access. Getting around that is out of scope by design.
- Last command and result: see evidence.
- Next step: none here. Follow-up: TASK-20261013-01-rentradar-listing-feed-partner.

## Related tasks

- TASK-20261013-01-rentradar-listing-feed-partner
