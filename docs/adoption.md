# Adopting agentproof in 15 minutes

## Solo developer

1. **Install and initialise** (2 minutes)

   ```bash
   pip install git+https://github.com/whoisthisadam/agentproof
   cd your-project
   agentproof init
   ```

   This adds `AGENTS.md`, `CLAUDE.md`, `PROTOCOL.md`, `docs/agentproof/`, `templates/`, `tasks/`, `knowledge/INDEX.md`, `inventory/hosts.yaml` and `.claude/settings.json`. Existing files are never overwritten; `init` prints what to merge by hand.

2. **Write one knowledge doc** (5 minutes). Copy `templates/knowledge-doc.md` to `knowledge/<your-product>/00-overview.md`. Fill in what the product is, how to build and test it, how it is deployed and where it runs. Unknown is fine; write "unknown".

3. **Describe your servers** (5 minutes, skip if you have none). One entry per host in `inventory/hosts.yaml`: alias, role, environment, fingerprint check, `protected` flag. Keep users, ports and keys in `~/.ssh/config`. Put a host-id file on each host so the fingerprint check has something to read:

   ```bash
   echo "build-runner-01" | sudo tee /etc/agentproof/host-id
   ```

4. **Give your agent its first task** (3 minutes). Ask for something small. Watch it create the task, fill the contract and stop for your review. Read the contract, approve, let it run, read the evidence.

Run `agentproof validate` in CI (see `.github/workflows/ci.yml` in this repo for an example) so the paperwork can't drift.

## Team

Same as above, plus:

1. **Agree on tiers** for your environments: what is production, which hosts are `protected`, who may approve Tier 2.
2. **Reviewer for Tier 2.** Someone other than the person who ran the agent reviews the plan before execution and the evidence afterwards.
3. **Task folders are shared.** Commit them by name (`git add tasks/<task-id>/`), never with `git add -A`. Raw data goes into the task's `data/` folder, which is gitignored.
4. **One agent key per environment**, owned by the team, not by a person. See [remote-access.md](remote-access.md).
5. **Ledger conflicts** disappear because the ledger is generated: on a merge conflict in `tasks/README.md`, take either side and run `agentproof ledger`.

## What to skip at first

- Journaling every command with `agentproof run`. Start by writing evidence by hand; add the journal when you start doing infrastructure work.
- Runbooks and ADRs. Write the first one after your first incident or your first "why did we do this?".
- Environment profiles. One `lab` profile is enough until you touch production.

## Using it with different agents

| Agent | Entrypoint it reads |
|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md`, plus `.claude/settings.json` and `.claude/skills/` |
| Codex, Cursor, Copilot agents and most others | `AGENTS.md` |
| Anything else | Put "Read AGENTS.md first" in its system prompt or rules file |
