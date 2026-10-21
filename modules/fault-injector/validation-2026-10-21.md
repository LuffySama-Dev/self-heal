# Random injector validation — 21 October 2026

The non-root development command completed a random live run successfully. No coordinator repair or reset was needed. The program selected and qualified a source mutation, deployed it to payment-repair-lab, supplied traffic, detected Hermes's verified deployment and waited for both firing and recovery sessions to complete. It then exited successfully and stopped its traffic. The repaired lab remains running.

- Result: `recovered_by_hermes`.
- Run: `20261021T093158Z-c1757a`.
- Fault injected: 2026-10-21T09:32:12.684851+00:00 (UTC).
- Verified deployment: 2026-10-21T09:39:18Z (UTC).
- Completed: 2026-10-21T09:49:13.519573+00:00 (UTC).
- Post-deployment traffic: **234 successful calls, 0 errors**.
- Before-fix regression results: 6 passed, 5 failed. After fix: 11 passed in each of UTC and America/Los_Angeles. Deployment helper passed six real gRPC probes.
- Four operator candidates qualified against the actual image; healthy baseline passed six of six probes. Nine unit tests passed, including compile/no-effect/startup rejection, overlapping-run rejection and cleanup after failed injection. Cleanup tests use mocks; no failed live rollout was forced.
- Source changes use no feature flags. Hermes access, alert thresholds and deployment helper were unchanged.

Evidence remains in `${HOME}/.local/state/self-heal-injector/20261021T093158Z-c1757a`; no private reasoning or credentials exported. Root-only installation remains a user-run sudo step and has not been performed. This is a practical workflow test with an accessible development checkout and prior source history, not a strictly blind benchmark. Scope is one payment adapter and four transformations, not arbitrary services or arbitrary code faults.

## User-run installed command

The user subsequently ran the installed root-only command. Independent observation confirmed an active root injector, a new firing webhook (`session-016`), Hermes's repair of a reversed validity guard, and deployment `20261021T104716Z` with `deployed_verified` at 10:47:26 UTC. The existing 11-case suite failed before repair; Hermes added Mastercard coverage and passed all 12 cases in both timezones. Deployment passed six live gRPC checks.

SigNoz resolved the incident at 10:54:25 UTC. Recovery session `session-017` completed, independently reporting 54 post-resolution successful server spans and zero errors. Both sessions ended `webhook_complete`; the injector process exited. The final observed five-minute window contained 120 calls and zero errors. The agent did not inspect root-only injector records or change its access; process exit status was not captured by this observer. Readable independent evidence is in `${PROJECTS_DIR}/incident-live-data/operator-run-observations.jsonl` and the two session response files in that directory. No coordinator repair/reset was performed.
