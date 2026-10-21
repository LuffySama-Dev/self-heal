# Automatic failure-to-recovery drill — 20 October 2026

**Passed: after fault injection, Hermes diagnosed, patched, tested, deployed and confirmed recovery without a human approval prompt or coordinator repair/deployment.**

This was the isolated payment-repair-lab, not the main demo or production. The coordinator injected the known expiry defect and supplied bounded restart-tolerant traffic, then observed. Existing regression tests, prior reports and git history remained visible. This verifies execution of a known self-healing workflow, not blind diagnostic performance or general production readiness.

## Evidence

Hermes correlated traces and logs, used Graphify and source inspection, reproduced the defect with **4 failing and 7 passing regression tests**, and changed the expiry comparison from `>=` to `>`. All 11 tests then passed in UTC and America/Los_Angeles, locally and inside the payment image.

Hermes invoked the pre-authorized deploy_lab.py command itself. It deployed the candidate, verified its hash and passed six real gRPC checks. The deployed source SHA-256 was `0b69b56d3d1151f5e9e2bf5f130d5fab49199afa4692f2112f3a208c493e4d80`.

The independent continuing replay recorded **318/318 successful calls after rollout completion, zero errors**. These are separate from the helper's six deployment checks. Calls exercised both current-month and future-year dummy cards.

In its firing session, Hermes independently found 246 successful post-deployment Charge spans and zero errors, and confirmed that the enabled alert became inactive. It then received the actual resolved notification and independently verified 90 successful post-resolution spans with zero errors, correlated a successful trace and log, checked transaction metrics and reran regression tests. It did not redeploy on recovery.

## Timeline (IST, Asia/Calcutta)

| Event | Time |
|---|---|
| Source defect injected | 15:27:14 |
| SigNoz firing timestamp | 15:32:25 |
| Firing notification accepted by Hermes | 15:32:55 |
| Hermes started deployment helper | 15:34:08 |
| Deployment verified | 15:34:26 |
| SigNoz resolved timestamp | 15:40:25 |
| Resolved notification accepted by Hermes | 15:42:55 |

From firing-notification receipt to verified deployment: approximately **1 minute 31 seconds**. SigNoz's firing-to-resolution interval was **8 minutes**; the resolved notification arrived **2 minutes 30 seconds** after resolution. These are single-run observations, including configured alert delays, not benchmark averages.

## Scope and limitations

The one-line source defect was deliberately injected; feature-flag fault injection stayed off. The original alert configuration, flags, regression suite and deployment helper hashes were unchanged during the drill. Hermes hit two blocked inspection commands and continued using other available operations without an approval request. The authorized deployment command itself was not blocked.

No rollback was needed; rollback behavior was tested previously with mocks, not exercised by a live failed rollout here. Unit tests use dependency stubs; live probes cover the selected payment cases. Success establishes recovery over the observed interval, not indefinite reliability.

The coordinator stopped temporary traffic only after both Hermes sessions completed. Fixed lab containers remain running and the lab alert is enabled/inactive. No sudo, production changes, commits or pushes occurred. Docker access is broad at the OS level; lab scoping remains the helper's fixed target plus agent instructions.

## Reproducible records

- Firing/repair session: `session-006`.
- Recovery session: `session-007`.
- Full evidence: `${PROJECTS_DIR}/payment-repair-drill/automatic-drill-20261020/`.
- Deployment originals: `${PROJECTS_DIR}/payment-repair-drill/deployments/20261020T100408Z/`.

The evidence includes actual payloads, relay HTTP 202 records, observable tool calls, responses, test output, deployment snapshots, source hashes, request outcomes and telemetry aggregates. Private model reasoning and credentials are not exported. Nothing has been published.
