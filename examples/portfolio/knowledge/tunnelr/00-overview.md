---
last-verified: 2026-09-22
verified-by: TASK-20260921-01-tunnelr-add-node-toronto
verified-against: tunnelr@e5a1f42 (main)
---

# Tunnelr: overview

## What it is

A consumer VPN. Users pick a region in the app; the control plane hands them a WireGuard config for an exit node in that region. About 1,200 paying subscribers.

## Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| Control plane API | `tunnelr` (`cmd/control`) | Go 1.23, PostgreSQL | Swarm stack `tunnelr` on `swarm-mgr-01` |
| Node agent | `tunnelr` (`cmd/nodectl`) | Go, WireGuard kernel module | each exit node, systemd unit `tunnelr-node` |
| Infrastructure | `tunnelr-infra` | Terraform | hosting provider API |
| Monitoring | `tunnelr-infra/monitoring` | Prometheus, Grafana, Alertmanager | Swarm stack `monitoring` on `swarm-mgr-01` |

## Deploy

- Control plane: tagged release → `docker service update` on `swarm-mgr-01` (Tier 2).
- Nodes: see [10-nodes.md](10-nodes.md). Adding or removing a node is Tier 2 (public DNS, customer traffic).

## Environments

| Environment | URL | Hosts |
|---|---|---|
| production | `https://api.tunnelr.example.com` | `swarm-mgr-01`, exit nodes |
| lab | `https://lab-api.tunnelr.example.com` | `build-runner-01` |

## Facts

```yaml
regions: {value: [fra, nyc, sgp, tor], how: measured, observed_at: 2026-09-22, source: TASK-20260921-01-tunnelr-add-node-toronto}
peers_per_node_alert: {value: "warn above 450 active peers", how: measured, observed_at: 2026-09-22, source: "tunnelr-infra@c02b7d1 alert rules"}
```

## Known traps

- The fra, nyc and sgp nodes predate the inventory and are managed only through Terraform and `nodectl` over the control plane. The agent has no SSH access to them by design. `tor-01` is the first node with an agent key.
