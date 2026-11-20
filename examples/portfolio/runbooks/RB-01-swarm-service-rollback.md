---
last-verified: 2026-09-10
verified-by: TASK-20260909-01-pulse-postgres-16-migration
verified-against: tunnelr-infra@c02b7d1 (main)
---

# RB-01: roll back a Swarm service to its previous image

**When to use:** a service on `swarm-mgr-01` or `build-runner-01` misbehaves after an update (failing health checks, error rate up, restarts climbing).
**Tier:** 1 on `build-runner-01`, 2 on `swarm-mgr-01`.
**Pre-approved for agents:** yes, for incident mitigation, when the service was updated in the last 24 hours. Record the incident in a task as soon as the rollback is done.

## Preconditions

- [ ] `agentproof fingerprint <host>` is OK.
- [ ] The service has a previous spec: `docker service inspect <svc> --format '{{json .PreviousSpec}}'` is not `null`.
- [ ] The update did not include a database migration. If it did, stop: rolling back the image does not roll back the schema. Hand over to the human.

## Steps

1. Record the current state: `docker service ps <svc> --no-trunc | head -20` and the current image.
2. Roll back: `docker service update --rollback <svc>`.
3. Wait for convergence: `docker service ps <svc>` until all replicas are `Running` on the previous image.

## Verify

- The service's health endpoint returns 200 from the host (`curl -fsS http://127.0.0.1:<port>/health`).
- Error rate in Grafana is back to the pre-update baseline within 10 minutes.
- Negative: `docker service ls` shows every other service with the same replica counts as step 1.

## Roll back

- Roll forward again with `docker service update --image <new-image> <svc>` once the fix is known.

## History

- TASK-20260909-01-pulse-postgres-16-migration: precondition about migrations added.
