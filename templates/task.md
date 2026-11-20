---
id: TASK-YYYYMMDD-NN-slug
title: <short title>
status: draft
tier: 1
product: <product>
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner: <who owns this task>
---

# <title>

## Goal

<One or two sentences: the observable end state, and why it matters.>

Request: "<the human's request, verbatim>"

## Scope

Touch:
- <paths, services, hosts that may change>

Do not touch:
- <tempting-but-wrong moves for this task>

Read only:
- <what will be read but not changed>

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| <repo@branch / host alias / environment> | <repo / host / db / cluster> | <value or "n/a for code-only"> | |

## Plan

1. <step> (tier <n>). Dry run: `<command>`. Execute: `<command>`.
2. ...

## Rollback

- How: <concrete commands or runbook, e.g. "redeploy image tag X">
- Tested: <yes / no, and why not>
- Point of no return: <the step after which rollback means fix forward, or "none">

## Acceptance criteria

- [ ] <checkable statement>

## Verification

- Boundary checks: <commands>
- Negative checks: <what must stay unchanged, and how to check it>
- Watch afterwards: <duration and what to watch, or "none">

## Approvals

<Required for tier 2 before execution. Delete for tier 0/1.>

- Approved by:
- When:
- Exact scope:
- Their words:

## Handoff

<Required while in-progress or blocked.>

- State now:
- Last command and result:
- Next step:
- Open questions:

## Related tasks

- <full task IDs, or "none">
