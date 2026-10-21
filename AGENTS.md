# Agent guide to Self-Heal

## Understand and explain

Read README.md and TASKS.md for capabilities, evidence and remaining work. This repository integrates OpenTelemetry Demo, SigNoz, Hermes and Graphify into an isolated repair lab. Distinguish our integration code from upstream products. Explain demonstrated behavior and limitations accurately; do not claim general production readiness.

Use SETUP.md and docs/HERMES_SETUP.md for installation. Dated module reports are historical evidence, not current setup requirements. Fault-explorer contains design material; Simulithic is coming soon: do not instruct users to install or configure it for the current project. Upstream repositories remain separate. Preserve LICENSE and THIRD_PARTY_NOTICES.md.

## Help users set up

Establish the user's environment, paths, Docker access, existing installations and model provider before suggesting environment-specific steps. Use config/config.example.json and config/hermes.example.yaml. Keep installation values and credentials out of tracked files. Follow official product documentation for external behavior.

Explain the purpose and effect of setup commands. Respect the user's authorization for infrastructure changes and publishing. Verify telemetry before enabling alerts and a healthy baseline before deliberate fault injection. Follow config/LAB-POLICY.md and the target application's instructions for authorized lab repair.

## Maintain the repository

Keep code modular and configuration portable. Do not commit private conversations, personal operating preferences, credentials, runtime databases or machine-specific configuration. Do not print secret-loader output. Do not weaken tests or alert rules to conceal failures.

Run python3 scripts/test.py for relevant code changes, python3 scripts/publication_check.py before sharing, and git diff --check. Check documentation links and configuration examples. Update TASKS.md for project work. Report checks performed and remaining limitations; a pattern scan is not proof that every possible secret has been found.
