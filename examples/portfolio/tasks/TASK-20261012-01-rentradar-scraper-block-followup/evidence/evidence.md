# Evidence: TASK-20261012-01-rentradar-scraper-block-followup

## Summary

The 403s are not a bug on our side. On 2026-10-10 the site added a `Disallow: /` for all user agents except search engines to robots.txt, and its terms now forbid automated collection. The only ways to keep scraping would be evasion, which the task rules out. Status: failed, with a follow-up for a licensed feed.

## Commands and observations

```text
$ ssh build-runner-01 'docker service logs --since 72h rentradar_scrapers 2>&1 | grep source3 | awk "{print \$5}" | sort | uniq -c'
   4120 status=403
      0 status=200
(first 403: 2026-10-10 06:14 UTC; last 200: 2026-10-10 06:09 UTC)

$ curl -s https://listings-three.example.org/robots.txt
User-agent: *
Disallow: /
User-agent: search-engine-bot
Allow: /

# Wayback-style snapshot from our own cache of robots.txt (2026-10-01): "Disallow: /account/" only.
# Terms page, section "Automated access", changed 2026-10-10: automated collection not permitted without a written agreement.
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Source 3 returns listings without evasion | staging scraper run | listings > 0 | not attempted: access is disallowed by the site | FAIL |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Sources 1 and 2 | listing counts, 3 days before vs after | within ±5% |
| Production config | `docker service inspect rentradar_scrapers` on `swarm-mgr-01` (read only) | unchanged |

## Not verified

- Whether the site offers a paid or partner feed: that's the follow-up.

## Knowledge updated

- `knowledge/rentradar/00-overview.md`: fact `sources_active` = 2; trap explaining the block and the no-evasion rule.

## Follow-ups

- TASK-20261013-01-rentradar-listing-feed-partner
