---
id: TASK-20260921-01-tunnelr-add-node-toronto
title: Add a Tunnelr exit node in Toronto (tor-01)
status: done
tier: 2
product: tunnelr
created: 2026-09-21
updated: 2026-09-22
owner: adam
---

# Add a Tunnelr exit node in Toronto (tor-01)

## Goal

A new WireGuard exit node `tunnelr-node-tor-01` serves the `tor` region: users who pick Toronto get a working tunnel whose egress IP is the node's address, the node is monitored, and `tor.vpn.tunnelr.example.com` resolves to it. It matters because Canadian users currently go through `nyc`, and 14 support tickets in August mentioned streaming geo-blocks.

Request: "Let's open Toronto. Same size as the other nodes. I'll do the SSH key myself."

## Scope

Touch:
- `tunnelr-infra/nodes/regions/tor.tfvars` (new) and Terraform state for `module.node["tor-01"]`
- Host `tunnelr-node-tor-01` (new): WireGuard and `tunnelr-node` configuration
- Control plane: register and activate node `tor-01` (via `nodectl`)
- DNS record `tor.vpn.tunnelr.example.com` (new)
- Prometheus scrape config for the new node (`tunnelr-infra/monitoring/targets/nodes.yml`)
- `swarm-mgr-01`: Prometheus config reload only (SIGHUP to the `monitoring_prometheus` container), nothing else
- `inventory/hosts.yaml` entry facts, `knowledge/tunnelr/*`

Do not touch:
- Existing nodes (`fra-01`, `nyc-01`, `sgp-01`) and their DNS records.
- Control plane image or database.
- Any other Terraform module: `terraform apply` is targeted at `module.node["tor-01"]` only.
- SSH keys and `authorized_keys` on the new host: human-only (Adam).

Read only:
- `swarm-mgr-01`, apart from the Prometheus reload (Grafana, Prometheus queries, control plane logs)
- Terraform state for the other nodes

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| Terraform workspace | IaC | `terraform workspace show` = `production` | yes, 2026-09-21 14:10 UTC |
| `tunnelr-node-tor-01` | host (production) | `cat /etc/agentproof/host-id` = `tunnelr-node-tor-01` | yes, 14:38 and 16:05 UTC |
| `swarm-mgr-01` | host (production; Prometheus reload only) | `cat /etc/agentproof/host-id` = `swarm-mgr-01` | yes, 14:12 UTC |
| DNS zone | DNS | zone `tunnelr.example.com`, provider account `tunnelr-prod` | yes, 15:52 UTC |

## Plan

1. Read current state (tier 0): `terraform plan` for the whole `nodes` root to confirm no drift; peer counts on existing nodes.
2. Write `regions/tor.tfvars`. Dry run: `terraform plan -target='module.node["tor-01"]'` → expect exactly 3 resources to add (server, firewall, floating IP), 0 change, 0 destroy (tier 2).
3. Apply the same targeted plan from the saved plan file (tier 2).
4. **Human step:** Adam adds `tunnelr-node-tor-01` to `~/.ssh/config`, installs the `agent-prod` key, adds the inventory entry.
5. `agentproof fingerprint tunnelr-node-tor-01`; check cloud-init finished; WireGuard and `tunnelr-node` running (tier 0).
6. `nodectl register --region tor --dry-run`, then register for real. Node starts in `draining` (no peers) (tier 2).
7. Test client: tunnel through `tor-01` with a test account; check egress IP and throughput (tier 1).
8. `nodectl activate tor-01` (tier 2).
9. Add Prometheus target; reload Prometheus (tier 1).
10. Publish DNS `tor.vpn.tunnelr.example.com A 203.0.113.41`, TTL 300 (tier 2). **Point of no return.**
11. Watch for 24 hours.

## Rollback

- How, before step 10: `nodectl deregister tor-01`, then `terraform destroy -target='module.node["tor-01"]'`. No customer has the endpoint yet.
- How, after step 10: remove the DNS record; drain with [RB-02](../../runbooks/RB-02-wireguard-node-drain.md); then deregister and destroy as above.
- Tested: the pre-DNS path was exercised on the lab control plane with a throwaway node on 2026-09-20 (register, deregister, destroy: clean). The post-DNS drain path is RB-02, last used 2026-07 on `fra-01`.
- Point of no return: step 10. Clients cache the record for up to 300 s and keep the endpoint in their saved config, so after it, removal requires a drain.

## Acceptance criteria

- [x] Terraform created exactly the 3 planned resources and changed nothing else.
- [x] Fingerprint of `tunnelr-node-tor-01` matches before and after the change.
- [x] A test client connected through `tor-01` sees egress IP `203.0.113.41`, and a 30 s download runs at more than 200 Mbit/s.
- [x] `tor-01` is `active` in the control plane and receives new peers.
- [x] Prometheus target `tor-01` is `up`; the node appears on the "Tunnelr nodes" dashboard.
- [x] `tor.vpn.tunnelr.example.com` resolves to `203.0.113.41` from two public resolvers.
- [x] 24 hours later: no alerts for `tor-01`, peers above 0, handshake errors below 1%.

## Verification

- Boundary checks: test-client tunnel and egress IP; `dig` from two public resolvers; Prometheus target state; peer count metric.
- Negative checks: `terraform plan` for the whole root shows no changes after apply; existing nodes' DNS records unchanged; existing nodes' peer counts not dropping by more than normal churn; control plane error rate unchanged.
- Watch afterwards: 24 h on the "Tunnelr nodes" dashboard and Alertmanager.

## Approvals

- Approved by: Adam
- When: 2026-09-21 14:05 UTC
- Exact scope: plan steps 2–3 (targeted Terraform apply, 3 resources) and 6–10 (register, activate, Prometheus target, DNS publish) for `tor-01` only; rollback as written. Step 4 is Adam's.
- Their words: "approved: tor-01, steps 2-3 and 6-10 as written, go. I'll do the key after the apply."

## Handoff

- State now: done. `tor-01` active since 2026-09-21 16:01 UTC, DNS published 16:12 UTC, 24 h watch passed.
- Last command and result: 2026-09-22 16:20 UTC, peers on `tor-01` = 87, no alerts in 24 h.
- Next step: none.
- Open questions: none.

## Related tasks

- none
