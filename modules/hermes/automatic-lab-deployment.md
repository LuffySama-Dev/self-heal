# Automatic isolated-lab deployment

The user authorized unattended lab deployment on 20 October 2026. No per-fix human approval is required for payment-repair-lab. Main-demo and production deployment remain outside this scope.

The gateway systemd drop-in zz-docker-group.conf starts the existing keyring launcher through sg docker. The actual Hermes process now inherits Docker group 110. No sudo or group database changes were needed.

The exact command `python3 ${PROJECTS_DIR}/self-heal/modules/hermes/deploy_lab.py` is pre-authorized in Hermes command_allowlist. Default unattended denial remains for other flagged commands; global approval checks were not disabled. The SigNoz route and REPAIR-LAB.md now authorize automatic lab rollout after a reproduced defect and passing regression tests. Resolved events verify recovery rather than redeploying.

The helper serializes deployments, freezes candidate source, checks the lab image/mount, runs the regression suite in the payment image in UTC and America/Los_Angeles, saves the previous snapshot, restarts only payment-repair-lab, tests six real gRPC requests and checks the deployed source hash. Failure after deployment restores the previous snapshot and checks it; rollback failure is recorded explicitly. Rollback restores the previous version, which may itself contain the incident defect. Hermes is instructed to check SigNoz recovery separately.

This is workflow scoping, not OS isolation: Hermes runs as the service user with Docker access and can write these user-owned files. Stronger isolation would require a separate deployment identity/service. The helper accepts no arbitrary target arguments.

## Verification

A temporary authenticated webhook route exercised the real Hermes worker, then was removed. Session session-003 completed without approval prompts. Hermes invoked the helper, which successfully redeployed the already-fixed snapshot: 11/11 tests in each timezone, 6/6 live gRPC checks, matching source hash. This was a deployment capability test, not a fresh defect-to-recovery drill. The earlier SigNoz recovery verification remains a separate result.

Three mocked failure-path tests passed: regression rejection preserves deployment, live-check failure rolls back, deployed hash mismatch rolls back. A live failed rollout was not deliberately induced.

Evidence: ${PROJECTS_DIR}/payment-repair-drill/deployments/20261020T095429Z/

Configuration backup: ${HOME}/.hermes/config.before-lab-autodeploy.yaml (private local file).

Official approval documentation: https://hermes-agent.nousresearch.com/docs/user-guide/security
