# Isolated payment lab: deployment and recovery verified

On 20 October 2026, the user approved deployment of Hermes's tested expiry fix to the isolated lab. The coordinator applied it; this was not an autonomous Hermes deployment. The main OTel Demo and production were unchanged.

## Result

The replay completed with **347 successful gRPC calls and zero failures**: 174 current-month cards and 173 future-year cards. Feature-flag fault injection remained off. The running container's charge.js SHA-256 matches the previously tested Hermes snapshot:

`0b69b56d3d1151f5e9e2bf5f130d5fab49199afa4692f2112f3a208c493e4d80`

The one-line change replaces the expiry comparison `>=` with `>`, accepting cards through their expiry month.

## Alert lifecycle (UTC)

- Restarted the paused faulty lab with bounded traffic and re-enabled its original, unchanged alert rule.
- Firing began at 09:37:25; Hermes accepted the firing webhook at 09:37:55.
- Applied the fixed snapshot and restarted only payment-repair-lab. First successful post-fix call: 09:38:23.
- SigNoz recorded resolution at 09:44:25 while successful traffic continued.
- Hermes accepted the resolved webhook at 09:47:55 (relay HTTP 202).
- Hermes completed recovery session `session-002` and independently queried 114 successful Charge server spans with zero errors in its post-resolution interval, 09:44:26–09:48:14 UTC. It also correlated successful traces/logs and transaction metrics.

The resolved payload references the same incident start and lab rule `instance-id-001`. Notification arrival was 3 minutes 30 seconds after the resolution timestamp. Clearing did not depend on stopping traffic: the replay continued until 09:49:57.

## Limits and final state

Hermes still could not inspect Docker through its unattended command policy. Its report correctly limits its own claim to observed recovery. The coordinator separately verified deployed source identity and the controlled request inputs. This demonstrates an approved lab rollout and observed recovery, not autonomous production deployment or long-term reliability.

The fixed lab containers remain running, the lab alert remains enabled/inactive, and the temporary traffic process has stopped. Main-demo traffic continues unchanged. No sudo, commits, pushes, or production rollout occurred.

Evidence: `${PROJECTS_DIR}/payment-repair-drill/recovery/` contains request records, source hashes, alert-state samples, firing/resolved payloads, relay acceptance logs and both Hermes responses. The namespace-filtered telemetry query is saved separately from Hermes's own service-filtered results.
