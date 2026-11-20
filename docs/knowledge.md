# Knowledge: how the agent remembers

Agents forget everything between sessions. The repository remembers, in three layers with different jobs:

| Layer | Holds | Changes |
|---|---|---|
| `knowledge/` | How each product works **now**: architecture, build, deploy, environments, known traps | Rewritten whenever a fact changes |
| `inventory/hosts.yaml` | Which machines exist, their role, fingerprint check and protection flag | When a machine is added, removed or changes role |
| `tasks/` | What was done, when and with what result | Never rewritten after closing |

Plus two supporting folders: `runbooks/` (approved procedures, especially for incidents) and `decisions/` (ADRs: why something is the way it is).

## Lookup order

1. `knowledge/INDEX.md`, then the product's docs and the inventory.
2. Only if the answer isn't there: the ledger, then the relevant task evidence. Newer tasks override older ones; a current knowledge doc overrides both.
3. Only then the live system.

Reaching step 2 or 3 for a fact the next session will also need means the knowledge doc has a gap. Fill it as part of the work.

## The staleness stamp

Every knowledge doc starts with:

```yaml
---
last-verified: 2026-09-15
verified-by: TASK-20260914-03-pulse-flaky-reminder-test
verified-against: pulse-api@4f2a9c1 (main)
---
```

- `last-verified`: when someone last checked the doc against reality.
- `verified-by`: the task that did it (full ID), or the source if no task applies.
- `verified-against`: the repository and commit the doc describes.

`agentproof validate` warns when a doc is older than 90 days and fails when `verified-by` names a task that doesn't exist.

If the branch you work on has moved past `verified-against`, the doc is a hypothesis. Check the parts you depend on before relying on them.

## Facts carry their source

For anything non-obvious (versions, sizes, limits, who owns what):

```yaml
postgres_version: {value: "16.4", how: measured, observed_at: 2026-09-10, source: TASK-20260909-01-pulse-postgres-16-migration}
dealer_quota:     {value: "600 req/min", how: reported, observed_at: 2026-08-26, source: "DealerHub CRM partner docs"}
```

- `measured`: we read it ourselves. Needs `observed_at`.
- `reported`: a person, ticket or vendor said it. A version number from a ticket is never `measured`.
- `inferred`: deduced from other facts.
- Unknown stays `null` with a note. Never guess.

A measured fact older than 30 days, or older than a newer task on the same system, is stale. Re-read it before relying on it.

## Update after every iteration

An iteration is any step that establishes, changes or disproves a fact. After each one:

1. Find the docs that describe what changed: `knowledge/INDEX.md`, then grep the product folder for the names involved (service, branch, version, host).
2. Correct those sections. Remove what became false. Add what you learned.
3. Re-stamp the front matter of every doc you touched.
4. Run `agentproof validate`. Grep for other copies of the claim you corrected.

Not at the end of the session. Facts held back for a final write-up are lost to context limits, interruptions and parallel sessions.

## Agent memory

Some agents keep their own memory outside the repository (for example Claude Code's auto-memory). Use it for preferences and pointers ("Adam prefers small PRs", "Pulse docs are in knowledge/pulse"). Facts about systems belong in the repository, where they are reviewed and versioned. When the two disagree, the repository wins and the memory entry gets corrected.

## Anti-patterns

- **Changelogs inside facts.** "Updated 09-12: … previously 09-03: …" comments grow forever. Git has the history; the doc holds the current state.
- **Copying task evidence into docs.** Distil it. The doc states the fact and links the task.
- **Keyword soup indexes.** `knowledge/INDEX.md` has one row per product with 5–10 words people actually use. If it needs more, the product needs more docs.
