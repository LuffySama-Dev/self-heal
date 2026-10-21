# Multi-service injector validation — 21 October 2026

## Scope

Version 2 supports three lab services and nine bounded source transformations: four Payment, three Recommendation and two Quote. Service selection is uniform, then a compatible transformation is selected. No feature flags are changed. Main demo source and containers are outside the repair scope. Tests below pin services and seeds for coverage; normal runs default to random service selection.

## Qualification

Healthy Recommendation and Quote baselines passed three real requests each. All five new transformations passed syntax checks, started, and failed all three behavior/latency probes. Candidates run with telemetry disabled. Evidence: `${HOME}/.local/state/self-heal-injector/qualification-v2/results.json`.

14 injector/runtime unit tests and nine evidence-adapter tests passed. All 13 dashboard panels queried successfully; the corrected internal-error chart was revalidated separately.

## Recommendation: completed

Run: `20261021T110604Z-84897b`, seed 0, catalog method mismatch. Two `ListProducts` calls became nonexistent `GetProducts` calls; Python compiled but requests failed. Hermes independently changed the calls back, added a regression test, passed candidate/live probes, deployed, and verified recovery. No coordinator application-source repair occurred.

- Injection: 11:06:29 UTC.
- Alert firing: 11:13:04 UTC.
- Hermes receipt: 11:18:34 UTC.
- Verified deployment: 11:20:20 UTC (three candidate and three live checks).
- Alert resolution: 11:27:04 UTC.
- Recovery receipt: 11:28:34 UTC; both Hermes sessions completed.
- Injector PASS: 11:29:37 UTC; 165 post-deployment calls, zero failures.

Evidence: `${HOME}/.local/state/self-heal-injector/20261021T110604Z-84897b/result.json`, its `traffic.jsonl`, and `${PROJECTS_DIR}/self-heal-labs/recommendation/deployments/20261021T112013Z/result.json`. Sessions: `session-012` and `session-013`.

This development run includes integration repairs and must not be published as an uninterrupted latency benchmark. The first detector missed Recommendation internal exceptions because its outer gRPC span did not set error status. The alert/chart now correlate kind=1 exceptions to server traces, excluding flagd client errors. Restarting Hermes also exposed profile-scoped credential loading: the inherited signing-key environment was insufficient. The documented command secret source now reads the existing GNOME Keyring credential into the profile. Real notification retries succeeded afterward; no fake notification or bypass was used. No secret is persisted in repository/config.

## Quote: completed

Run `20261021T112939Z-fe0125`, seed 0, blocking-latency: `usleep(1500000)` before quote calculation. PHP compiled and requests returned correct totals, but exceeded the one-second limit. Hermes used Graphify, found and removed the delay, added `src/quote/test_quote_latency.py`, and deployed via the approved helper. One ad hoc shell check was blocked by existing unattended command policy; Hermes proceeded through approved commands without widening permissions.

Firing session: `session-014`, received 11:35:15 UTC. Verified deployment completed 11:37:15 UTC; three candidate and three live checks passed. Live checks took approximately 0.4–23 ms. Deployment evidence: `${PROJECTS_DIR}/self-heal-labs/quote/deployments/20261021T113711Z/result.json`.

Both firing investigations used Graphify: Recommendation query_graph/get_neighbors, Quote query_graph. This verifies use, not a measured speed benefit.

The normal alert evaluator includes a two-minute evaluation delay in addition to its rolling query windows. Both firing and recovery sessions completed successfully. Injector PASS at 2026-10-21T11:46:58.029145+00:00; 174 post-deployment calls, zero failures. Recovery session: `session-015`. Run/traffic evidence: `${HOME}/.local/state/self-heal-injector/20261021T112939Z-fe0125/`.

Observed notification timestamps: alert firing 2026-10-21T11:34:45.100433441Z; alert resolution 2026-10-21T11:43:45.100433441Z; recovery receipt 11:45:15 UTC. Quote completed without coordinator integration or application-source intervention during its live run.
