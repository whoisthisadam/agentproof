# FAQ

**Why not just a good `CLAUDE.md`?**
A rules file tells the agent how to behave in one session. agentproof also leaves a trail: the contract you approved, the commands that ran, what was observed, and what the next session needs. Instructions don't survive the session; files do.

**Doesn't this slow the agent down?**
For small things, barely: a Tier 1 one-line fix gets a ten-line task. For risky things it slows down exactly the step that should be slow, which is the human approval. Most time saved comes later, when nobody has to reconstruct what happened.

**Do I need the CLI?**
No. The protocol works with markdown files alone. The CLI scaffolds tasks, generates the ledger, journals commands and checks that nothing drifted. `validate` in CI is the part most worth keeping.

**What needs a task and what doesn't?**
Anything that changes code, config, a host or data needs a task. Answering a question, reading code, reviewing the repository's own docs or running tests locally doesn't. Ask: would a stranger need this record to understand the state of a system? If not, skip the task.

**Can the agent approve its own Tier 2?**
No. The approval comes from the human, in the session, and is written into the task with their words.

**What about multiple agents in parallel?**
One task per agent, separate worktrees, separate *Scope → Touch* lists that don't overlap. The generated ledger avoids merge conflicts on the index.

**Where does this come from?**
From running AI agents daily on several products: mobile apps, APIs, bots and self-hosted infrastructure. The [lessons](lessons.md) are the incidents that shaped the rules.
