# Evidence: TASK-20260921-01-tunnelr-add-node-toronto

## Summary

`tunnelr-node-tor-01` was created with a targeted Terraform apply (3 resources, nothing else changed), registered and tested in `draining` state, activated, added to monitoring, and published at `tor.vpn.tunnelr.example.com`. A test client tunnelled through it with the expected egress IP at 412 Mbit/s. After 24 hours it carried 87 peers with no alerts. Status: done.

## Commands and observations

Full journal: [journal.md](journal.md). The session ran with `AGENTPROOF_ENV=production`, set by Adam at 14:02 UTC, and the `agent-prod` key loaded from 14:35 UTC (after the human step) to 16:30 UTC.

**Orientation (14:10 UTC)**

```text
$ terraform -chdir=nodes workspace show
production
$ terraform -chdir=nodes plan -var-file=regions/all.tfvars -detailed-exitcode
No changes. Your infrastructure matches the configuration.
```

No drift before the change.

**Dry run and apply (14:14–14:21 UTC)**

```text
$ terraform -chdir=nodes plan -target='module.node["tor-01"]' -var-file=regions/tor.tfvars -out=tor-01.plan
Plan: 3 to add, 0 to change, 0 to destroy.
  + module.node["tor-01"].provider_server.this        (2 vCPU, 4 GB, region tor)
  + module.node["tor-01"].provider_firewall.this      (51820/udp, 9100/tcp from 192.0.2.10)
  + module.node["tor-01"].provider_floating_ip.this

$ terraform -chdir=nodes apply tor-01.plan
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
Outputs: tor_01_ipv4 = "203.0.113.41"
```

**Human step (14:22–14:35 UTC):** Adam added the SSH config entry and the `agent-prod` key, and the inventory entry.

**Host checks (14:38 UTC)**

```text
$ agentproof fingerprint tunnelr-node-tor-01
OK tunnelr-node-tor-01: tunnelr-node-tor-01

$ ssh tunnelr-node-tor-01 'cloud-init status; systemctl is-active wg-quick@wg0 tunnelr-node prometheus-node-exporter'
status: done
active
active
active
```

**Register in draining state (14:44 UTC)**

```text
$ nodectl register --region tor --endpoint 203.0.113.41:51820 --name tor-01 --dry-run
would register: name=tor-01 region=tor endpoint=203.0.113.41:51820 state=draining
$ nodectl register --region tor --endpoint 203.0.113.41:51820 --name tor-01
registered tor-01 (state=draining)
```

**Test client (15:02 UTC)**, using the test account `qa-tor@example.com` on the lab laptop:

```text
$ tunnelr-cli connect --node tor-01 --account qa-tor
connected: handshake 0.21 s ago
$ curl -s https://ifconfig.example.net
203.0.113.41
$ curl -s -o /dev/null -w '%{speed_download}\n' --max-time 30 https://speedtest.example.net/1GB.bin
51521337
```

51.5 MB/s ≈ 412 Mbit/s. The download hit the 30 s limit as intended; the rate is computed over the transferred part.

**Activate, monitor (15:58–16:05 UTC)**

```text
$ nodectl activate tor-01
tor-01: draining -> active

$ ssh swarm-mgr-01 'curl -s 127.0.0.1:9090/api/v1/targets | jq -r ".data.activeTargets[] | select(.labels.node==\"tor-01\") | .health"'
up

$ agentproof fingerprint tunnelr-node-tor-01
OK tunnelr-node-tor-01: tunnelr-node-tor-01
```

**DNS (16:12 UTC, point of no return)**

```text
$ dnsctl record add tunnelr.example.com tor.vpn A 203.0.113.41 --ttl 300 --dry-run
would add: tor.vpn.tunnelr.example.com. 300 IN A 203.0.113.41 (zone serial 2026092104 -> 2026092105)
$ dnsctl record add tunnelr.example.com tor.vpn A 203.0.113.41 --ttl 300
added
$ dig +short tor.vpn.tunnelr.example.com @resolver1.example.net
203.0.113.41
$ dig +short tor.vpn.tunnelr.example.com @resolver2.example.org
203.0.113.41
```

**24-hour watch (until 2026-09-22 16:20 UTC)**

```text
tunnelr_node_active_peers{node="tor-01"}            87
rate(tunnelr_node_handshake_errors_total{node="tor-01"}[24h]) / rate(tunnelr_node_handshakes_total{node="tor-01"}[24h])   0.0031
Alertmanager: 0 alerts with node="tor-01" in 24 h
```

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | Exactly the 3 planned resources | `terraform apply` output + full `plan` afterwards | 3 added, then no changes | 3 added; full plan: no changes | PASS |
| 2 | Fingerprint before and after | `agentproof fingerprint` at 14:38 and 16:05 | match | OK both times | PASS |
| 3 | Egress IP and throughput | test client, `ifconfig.example.net`, 30 s download | 203.0.113.41, > 200 Mbit/s | 203.0.113.41, 412 Mbit/s | PASS |
| 4 | Active and receiving peers | `nodectl status tor-01` at 16:40 | active, peers > 0 | active, 9 peers | PASS |
| 5 | Monitored | Prometheus target health, dashboard | up, visible | up, visible | PASS |
| 6 | DNS resolves | `dig` from two resolvers | 203.0.113.41 | 203.0.113.41 from both | PASS |
| 7 | Healthy after 24 h | peers, error ratio, alerts | peers > 0, < 1%, 0 alerts | 87, 0.31%, 0 alerts | PASS |

## Negative checks

| What must be unchanged | Check | Observed |
|---|---|---|
| Other Terraform resources | `terraform plan -var-file=regions/all.tfvars` after apply | No changes |
| Other nodes' DNS | `dig +short {fra,nyc,sgp}.vpn.tunnelr.example.com` before (14:11) and after (16:15) | identical |
| Other nodes' peers | `tunnelr_node_active_peers` for fra/nyc/sgp, 15:30 vs 17:30 | nyc −41 (users moving to tor, expected), fra +3, sgp −1 (normal churn) |
| Control plane | 5xx rate on `api.tunnelr.example.com`, 1 h before vs 1 h after | 0.02% vs 0.02% |
| Test account removed | `tunnelr-cli account delete qa-tor` at 16:25, then `account show qa-tor` | "not found" |

## Not verified

- IPv6: the node has no IPv6 yet (no other node does either). Out of scope.
- Throughput under load from many peers at once: only one test client was used. The 24 h peer and error metrics cover real load at 87 peers.

## Knowledge updated

- `knowledge/tunnelr/00-overview.md`: regions now include `tor`; note that `tor-01` is the first node with an agent key; re-stamped.
- `knowledge/tunnelr/10-nodes.md`: procedure with the draining-first order, point of no return, DNS TTL, node size, `--region` default trap; re-stamped.
- `runbooks/RB-02-wireguard-node-drain.md`: history line; re-stamped.
- `inventory/hosts.yaml`: facts for `tunnelr-node-tor-01` (entry added by Adam in the human step).

## Follow-ups

- none
