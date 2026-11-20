# Secrets

## The model

```text
secret manager  ──(runtime injection)──►  process environment  ──►  CLI / API client
system of record                          exists only while running    the agent sees names, not values
```

An agent that reads a secret has it in its context window, and from there it can end up in a log, an evidence file, a commit or a chat. So: **the agent handles references; tools handle values.**

## Getting values into processes

Pick one, in order of preference:

1. **Secret manager runner**: `op run --env-file=.env.tpl -- <cmd>`, `doppler run -- <cmd>`, `sops exec-env secrets.enc.yaml '<cmd>'`. Values never touch the disk in plain text.
2. **Short-lived credentials**: cloud OIDC or workload identity, SSH certificates, tokens that expire in hours.
3. **A gitignored env file per environment** (`.env.lab`, `.env.production`), filled by the human from the secret manager. Never one file holding both.

`.env.example` documents every variable by **name and purpose**, with placeholder values like `changeme`.

## Rules for agents

1. Never open `.env*`, `*.pem`, `*.key`, `id_*` or credential files. `.claude/settings.json` denies these reads; don't work around it.
2. To see what is configured, run `agentproof env-check`. It prints names and set/unset only.
3. Never put a secret on a command line (it shows up in process lists and shell history). Pass it through the environment.
4. Refer to secrets as `$VARIABLE_NAME` in tasks, evidence and chat.
5. A missing secret makes the task `blocked`. Never go looking for credentials elsewhere.
6. If a value is ever exposed, stop, tell the human, and record a rotation follow-up. Exposure is never ignored.

## Rules for humans

- Rotate high-privilege credentials at least every 90 days and immediately after any exposure.
- One credential per purpose and per environment. Read-only identities for read-only work.
- Offboarding a machine revokes its SSH keys and tokens.

## Guard rails in this repository

| Guard | Where |
|---|---|
| Deny reads of secret files, deny `git push` | `.claude/settings.json` |
| Secret scan before every commit | `.pre-commit-config.yaml` (gitleaks) |
| Secret scan on every push and PR | `.github/workflows/ci.yml` |
| Redaction of journals | `agentproof run` and `agentproof redact` |
| Gitignored secret patterns and task `data/` folders | `.gitignore` |

Redaction is a safety net. It catches known variable values and common token shapes. It doesn't make handling values safe.

## Data is not a secret, but it is confidential

Data reached *through* a credential (database rows, customer emails, logs with user IDs) gets its own rule: describe it in evidence (counts, table names, IDs you generated), never copy it. A staging database seeded from production is real data.
