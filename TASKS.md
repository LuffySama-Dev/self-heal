# Self-Heal tasks

## Implemented lab

- [x] Run OTel Demo separately and export telemetry to self-hosted SigNoz.
- [x] Connect authenticated alert delivery to Hermes and SigNoz MCP.
- [x] Connect Graphify OSS for code investigation.
- [x] Add fixed-target validation and deployment helpers for Payment, Recommendation and Quote.
- [x] Verify automatic source repair, testing, deployment and recovery in lab drills.
- [x] Add nine bounded source mutations across the three services.
- [x] Add availability and missing-telemetry alerts.
- [x] Add Incident Live stages, incident counts and timing panels.
- [x] Record exploratory Graphify comparisons with limitations.

## Public repository preparation

- [x] Make installation paths, endpoints and rule IDs configurable.
- [x] Keep upstream OTel Demo code in a separate pinned checkout.
- [x] Add setup instructions and a dedicated Hermes walkthrough/config example.
- [x] Add MIT license and preserve upstream fixture notices.
- [x] Remove private operational records from the public file set and anonymize selected reports.
- [x] Add tests and publication scanning; verify clean-copy portability.
- [x] Document remaining limitations in docs/PUBLICATION_REVIEW.md.
- [ ] Test full setup on a fresh second host.
- [x] Review and authorize committing and pushing the prepared repository.
- [x] Owner made the repository public after the authorized commit/push.

## Further work

- [ ] Integrate Simulithic after hosted access is available.
- [ ] Expand repeated experiments before making general performance claims.
- [ ] Exercise live failed-rollout recovery and external monitoring of the observability/delivery stack.

Autonomous deployment scope remains the three isolated repair labs.

- [ ] Add incident coordination and isolated investigation workspaces; validate simultaneous multi-service failures.
