# Hermes code-repair trial — 20 October 2026

**Detection → investigation → patch → regression tests passed. The subsequent approved lab deployment and recovery verification also passed; see [recovery verification](payment-recovery-verification.md).**

We deliberately introduced an expiry-date comparison defect in an isolated
payment lab. Cards expiring this month were incorrectly rejected. This is a
source-code defect, not feature-flag fault injection or an organically discovered
production incident. The existing demo remained unchanged.

SigNoz fired the separate lab alert at 13:13:25 IST. Hermes received it at about
13:13:55 IST and used SigNoz MCP traces, logs and metrics plus local source access.
It correlated the failure with charge.js:87 and identified the incorrect `>=`
comparison. It restored the strict `>` comparison, preserving acceptance through
the expiry month. Its normal git history exposed the introduced change; this was
not a blind diagnostic benchmark.

```diff
- if ((currentYear * 12 + currentMonth) >= (year * 12 + month)) {
+ if ((currentYear * 12 + currentMonth) > (year * 12 + month)) {
```

Hermes wrote 11 regression tests: 4 failed before the fix and all 11 passed after
it, in two timezones. The coordinator independently reran all 11 inside the
payment image and passed an additional eight-case boundary suite (three of those
cases failed on the defective snapshot). These tests stub external dependencies;
they do not prove post-fix gRPC integration or telemetry recovery.

Hermes's unattended command policy blocked Docker access, despite terminal tools
being enabled. It used local Node without bypassing that policy. The coordinator
performed the disposable-container verification. Autonomous container rollout
is therefore not yet demonstrated.

At the end of the initial trial, the faulty lab containers were stopped and its temporary alert disabled, pending
review. This is experiment cleanup, not verified recovery. The original payment
alert remains separate. No sudo, commits, pushes or production deployments occurred.

## Review artifacts

- Patch: ${PROJECTS_DIR}/payment-repair-drill/proposed-fix.patch
- Source: ${PROJECTS_DIR}/otel-demo-repair-lab/src/payment/charge.js
- Tests: ${PROJECTS_DIR}/otel-demo-repair-lab/src/payment/charge.test.js
- Hermes report: ${PROJECTS_DIR}/otel-demo-repair-lab/REPAIR-REPORT.md
- Evidence: ${PROJECTS_DIR}/payment-repair-drill/

Subsequently approved and completed: apply this one-line fix to the isolated lab snapshot, restart its
test services and traffic, re-enable its alert, and verify successful requests and
healthy telemetry. No main-demo or production rollout is included.
