---
name: close-task
description: Close an agentproof task honestly - check every acceptance criterion has evidence, update knowledge docs, set the final status and regenerate the ledger.
---

# Close task

## Rules that bind this skill

- No evidence, no done. A criterion without an observed result is not met.
- Don't rewrite history: if earlier evidence was wrong, say so in a new line, don't edit the old one.
- Secrets and personal data never go into evidence.

## Procedure

1. Open `tasks/<id>/task.md` and `evidence/evidence.md`.
2. For each acceptance criterion, find the row in the evidence table. It needs a check, an expected result and an observed result. If a check was never run, run it now (if it's Tier 0) or mark the criterion as failed.
3. Confirm the negative checks ran. Fill **Not verified** honestly; "Nothing" only if true.
4. If a subagent drafted any part of the evidence, check each command and number against the journal or the session.
5. Update every knowledge doc and inventory entry the task changed. Re-stamp their front matter with this task's full ID. List them under **Knowledge updated**.
6. Cleanup: temporary resources, test data, open tunnels or sessions. Record what was cleaned.
7. Set the status:
   - `done`: every criterion passed and cleanup is done.
   - `failed`: the goal wasn't reached. Add the follow-up task under **Follow-ups**.
   - Otherwise it stays `in-progress` or `blocked`, with **Handoff** updated.
8. Update `updated:` in the front matter. Run `agentproof ledger` and `agentproof validate`. Run `agentproof redact` over anything pasted from tool output.

## Output

A short report: final status, criteria passed/failed, what was not verified, docs updated, follow-ups. Do not commit unless the human asks.
