# ADR-002: agents use their own SSH key per environment

- Status: accepted
- Date: 2026-09-18
- Decided by: Adam

## Context

Agents used Adam's personal SSH key, which works on every host. A task scoped to staging could technically reach production. Revoking agent access would have meant revoking Adam's.

## Decision

- Two agent keys: `agent-lab` (lab and staging hosts) and `agent-prod` (production hosts). Neither is Adam's key.
- `authorized_keys` entries are restricted with `from=` (the workstation's network) and `restrict,pty`.
- `agent-prod` is loaded into the SSH agent only for sessions with an approved Tier 2 task, and removed afterwards (`ssh-add -d`).
- The inventory holds aliases only; connection details stay in `~/.ssh/config`.
- Installing an agent key on a host is human-only.

## Consequences

- A lab session cannot reach production even by mistake: the key isn't loaded.
- One more step before production work: load the key. That step is intentional.

## Alternatives considered

- SSH certificates with short validity: better, planned once there are more than five hosts.
- No agent SSH at all: rules out the end-to-end workflow this setup exists for.
