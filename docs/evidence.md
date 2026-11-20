# Evidence

Evidence answers one question for a stranger: **what actually happened, and how do we know?**

## What counts

| Counts | Doesn't count |
|---|---|
| `curl -s -o /dev/null -w '%{http_code}' https://api.pulse.example.com/health` → `200` | "the API is healthy" |
| `pytest tests/reminders -p no:randomly --count 50` → `50 passed` | "tests pass now" |
| `docker service ps pulse_api` → 3/3 running, image `pulse-api:2.14.1`, 0 restarts in 30 min | "deploy succeeded" (exit code 0) |
| "Not verified: iOS push delivery; no test device available" | silence about what wasn't checked |

## Check at the boundary

A change is verified where its users would see it: the HTTP endpoint, the app screen, the SSH login, the test suite, the metric. A successful command proves the command ran, not that the change works.

## Negative checks

Every change verifies what should **not** have changed: other services still running, other tests still green, other hosts untouched, unrelated DNS records intact. Scope them to the realistic blast radius, and widen the scope once a host has surprised you. A cleanup command that should only touch stopped containers deserves a full-host check after it runs.

## The evidence file

Use [templates/evidence.md](../templates/evidence.md). Sections:

1. **Summary**: what changed, in two or three sentences.
2. **Commands and observations**: commands and the relevant part of real output. Redacted. If `agentproof run` wrote `journal.md`, link to it.
3. **Acceptance criteria**: one row per criterion from the task.

   | # | Criterion | Check | Expected | Observed | Result |
   |---|---|---|---|---|---|

4. **Negative checks**: what, how, observed.
5. **Not verified**: and why. "Nothing" is a valid entry; an empty section is not.
6. **Knowledge updated**: docs and inventory entries changed, or "none".
7. **Follow-ups**: new tasks with full IDs (required for `failed`).

## Traps

- **A failed check is not a negative result.** If a script fetches a log and searches it for an error, "no match" means nothing until you know the fetch returned the whole log. Check the status code, exit code or byte count of the fetch itself.
- **Fixed server, cached client.** After fixing one side of a client/server pair, restart or reconnect the other side and test again. A client holding an old connection can hide a fix, or hide that it didn't work.
- **Dry-run output is evidence.** Save it and compare it with what actually changed.
- **Idempotency.** Where possible, run the change a second time and confirm it reports "nothing to do".
- **Delegated write-ups.** A subagent may draft evidence. The task owner checks every command and number in it against what really happened. A plausible invented evidence file is worse than none.

## What never goes into evidence

- Secret values, tokens, full connection strings. Use `$VARIABLE_NAME`.
- Personal data: emails, names of end users, card or order numbers. Use counts and IDs you generated yourself.
- Raw dumps. Put them in the task's gitignored `data/` folder and summarise them.

Run `agentproof redact < file` on anything you paste, and let `gitleaks` check the commit.
