---
last-verified: YYYY-MM-DD
verified-by: TASK-YYYYMMDD-NN-slug
verified-against: <repo>@<short-sha> (<branch>)
---

# <Product>: overview

## What it is

<One paragraph: what it does and who uses it.>

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| | | | |

## Build and test

```bash
<commands that work today>
```

## Deploy

<How a change reaches each environment. Link the runbook if there is one.>

## Environments

| Environment | URL | Hosts (inventory aliases) |
|---|---|---|
| | | |

## Facts

<Non-obvious facts with their source.>

```yaml
example_fact: {value: "", how: measured, observed_at: YYYY-MM-DD, source: TASK-...}
```

## Known traps

- <things that cost time, with the task that found them>
