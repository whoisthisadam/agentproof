# Servers, SSH and production

The end-to-end development cycle doesn't stop at a merged PR. Code gets built, deployed to hosts and checked in production. This page covers how the agent reaches machines without being handed the keys to everything.

## Inventory holds identity, `~/.ssh/config` holds access

`inventory/hosts.yaml` (template: [templates/host.yaml](../templates/host.yaml)):

```yaml
hosts:
  - alias: tunnelr-node-tor-01
    role: WireGuard exit node, Toronto region
    product: tunnelr
    environment: production
    protected: false
    fingerprint:
      via: ssh
      command: cat /etc/agentproof/host-id
      expected: tunnelr-node-tor-01
    facts:
      public_ip: {value: 203.0.113.41, how: measured, observed_at: 2026-09-21, source: TASK-20260921-01-tunnelr-add-node-toronto}
```

Never in the inventory: `user`, `port`, `identity_file`, `password`, keys or tokens. `agentproof validate` rejects them. Those live in the human's `~/.ssh/config` (example: [templates/ssh_config.example](../templates/ssh_config.example)):

```text
Host tunnelr-node-tor-01
    HostName 203.0.113.41
    User agent-prod
    IdentityFile <YOUR_AGENT_PROD_KEY_PATH>
    IdentitiesOnly yes
    StrictHostKeyChecking yes
    ForwardAgent no
```

The agent only ever types `ssh tunnelr-node-tor-01 …`.

## Fingerprints

A fingerprint is a read-only command whose output proves the target is the right one. The simplest one that works everywhere: write the host's alias into `/etc/agentproof/host-id` when you provision it. Others:

| Target | Fingerprint command |
|---|---|
| Any Linux host | `cat /etc/agentproof/host-id` |
| Docker Swarm | `docker info --format '{{.Swarm.Cluster.ID}}'` |
| Kubernetes | `kubectl config current-context` (`via: local`) |
| Terraform | `terraform workspace show` (`via: local`) |
| Database | `SELECT current_database()` |

`agentproof fingerprint <alias>` runs the check and exits non-zero on mismatch. Run it before and after every Tier 1 or Tier 2 operation, and record both in evidence. "The default context happened to be right" is a failure, not a success.

## Keys

- **One agent key per environment** (`agent-lab`, `agent-prod`), separate from the human's own key. Revoking the agent never locks out the human.
- **Restricted `authorized_keys` entries:**

  ```text
  from="192.0.2.0/24",restrict,pty ssh-ed25519 <AGENT_PROD_PUBLIC_KEY> agent-prod
  ```

  Use `command="…"` when the agent only needs one operation on that host.
- **Passphrase plus an agent** for the human's key; the agent's key sits in the human's SSH agent only for the session that needs it, when practical.
- **No agent forwarding** (`ForwardAgent no`). Use `ProxyJump` through a bastion instead.
- **Strict host keys.** A changed host key is a stop-and-report event, never `accept-new` on a known host.

## Scope per task

The task's *Scope* lists every host it may change (*Touch*) or read (*Read only*). Other hosts are out of scope even if the key would work. Adding SSH access to a new host is itself a Tier 2 task, done by the human.

## Production

- Production changes are Tier 2: approval written into the task first.
- The human sets `AGENTPROOF_ENV=production` for the session. `agentproof run --mutating` refuses a production host while the session is in `lab`.
- Snapshot or backup before any Tier 2 step on a stateful system, and put the check in the evidence.
- Prefer orchestrator updates that roll back on their own (`docker service update --update-failure-action rollback`), and confirm the rollback path exists before the update.
- Use `127.0.0.1` rather than `localhost` in health checks on hosts where IPv6 loopback is unreliable. One less flaky signal.

## Shared hosts

If a host also runs things that aren't yours, write them into the host's `notes` in the inventory and the task's *Do not touch*. Never run host-wide cleanup (`docker system prune`, `iptables -F`, `stack rm`) on a shared host. Firewall and NAT changes on shared hosts are append-only: snapshot the rules, add yours, diff, and confirm that only your lines changed.

## Incidents

During an incident the agent may only run a runbook from `runbooks/`. Anything else is a proposal: the agent writes the exact commands, the human decides.
