---
last-verified: 2026-09-22
verified-by: TASK-20260921-01-tunnelr-add-node-toronto
verified-against: tunnelr@e5a1f42 (main)
---

# RB-02: drain a Tunnelr exit node

**When to use:** before restarting WireGuard or a node host, before removing a node, or when a node is unhealthy and still taking peers.
**Tier:** 2 (customer traffic moves).
**Pre-approved for agents:** yes, for an unhealthy node during an incident. Planned drains need approval in a task.

## Preconditions

- [ ] At least one other node in the same region, or another region below 70% of its peer alert threshold.
- [ ] `agentproof fingerprint <alias>` is OK (for nodes in the inventory).

## Steps

1. `nodectl status <node>`: record active peers.
2. `nodectl drain <node> --dry-run`: shows how many peers will be moved and where.
3. `nodectl drain <node>`: the control plane stops assigning new peers and pushes a config with another endpoint to connected clients.
4. Watch `tunnelr_node_active_peers{node="<node>"}` fall. Most clients move within 5 minutes; stragglers after 30 minutes are disconnected by `nodectl drain --finish`.

## Verify

- Active peers on the node: 0.
- Peers on the receiving nodes went up by about the same number; none crossed its alert threshold.
- Negative: the control plane error rate is unchanged.

## Roll back

- `nodectl activate <node>` returns it to service.

## History

- TASK-20260921-01-tunnelr-add-node-toronto: drain used as the rollback path after DNS publication.
