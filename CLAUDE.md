# CLAUDE.md

All agent instructions for this repository are in [AGENTS.md](AGENTS.md), which binds every session to [PROTOCOL.md](PROTOCOL.md). Read both before acting.

Two rules hold from the first message, before you have read anything else:

1. **No task, no change.** Reading is free. Anything that changes code, config, a host or data needs a task file in `tasks/` first (`agentproof new-task <slug>`), and Tier 2 needs the human's approval written into it.
2. **No evidence, no done.** Never report something as working without naming the command you ran and the result you observed. Write it into the task's `evidence/evidence.md`.

The deny rules in `.claude/settings.json` block reading secret files and pushing. Don't work around them; ask the human.
