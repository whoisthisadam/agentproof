---
last-verified: 2026-09-22
verified-by: TASK-20260921-01-tunnelr-add-node-toronto
verified-against: tunnelr-infra@c02b7d1 (main)
---

# Tunnelr: exit nodes

## Adding a node

1. `terraform -chdir=nodes plan -var-file=regions/<region>.tfvars` → review → `apply` (Tier 2).
2. Cloud-init installs WireGuard, `tunnelr-node`, node_exporter, and writes `/etc/agentproof/host-id`.
3. The human adds the host to `~/.ssh/config` and `inventory/hosts.yaml` and installs the agent's production key (human-only: access change).
4. `agentproof fingerprint <alias>`.
5. `nodectl register --region <region> --dry-run`, then without `--dry-run`. The node starts in `draining` state: it accepts no new peers.
6. Verify with a test client, then `nodectl activate`. Then publish DNS `<region>.vpn.tunnelr.example.com`.

DNS publication is the **point of no return**: clients cache the record for up to the TTL (300 s) and store the endpoint in their config. Before it, rollback is `nodectl deregister` + `terraform destroy`. After it, rollback is drain first ([RB-02](../../runbooks/RB-02-wireguard-node-drain.md)), then remove.

## Facts

```yaml
dns_ttl: {value: "300 s", how: measured, observed_at: 2026-09-21, source: TASK-20260921-01-tunnelr-add-node-toronto}
node_size: {value: "2 vCPU, 4 GB, 1 Gbit/s", how: measured, observed_at: 2026-09-21, source: TASK-20260921-01-tunnelr-add-node-toronto}
wireguard_port: {value: "51820/udp", how: measured, observed_at: 2026-09-21, source: TASK-20260921-01-tunnelr-add-node-toronto}
```

## Known traps

- `nodectl register` without `--region` defaults to `fra`. Always pass it; the dry run prints the region.
- The provider's firewall is separate from the host's `nftables`. Both need 51820/udp.
