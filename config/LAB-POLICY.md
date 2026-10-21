# Approved isolated repair labs

Read this checkout's AGENTS.md. Only payment-repair-lab, recommendation-repair-lab and quote-repair-lab are authorized for autonomous repair. Main demo and production are excluded. Do not commit or push, contact others, use sudo, modify credentials or permissions, or change alerts, flags, probes or deployment helpers to hide failures.

Use telemetry to identify the affected service. Inspect relevant source and Graphify relationships; graph nodes are not proof of deployed identity. Check the actual source mount and image. Reproduce, make a minimal repair if needed, add meaningful regression tests, validate, and deploy only through the matching fixed helper.

| Service | Editable application file | Validation | Deployment |
|---|---|---|---|
| Payment | src/payment/charge.js | Run charge.test.js in the pinned payment image, UTC and America/Los_Angeles. | `python3 <repo>/modules/hermes/deploy_lab.py` |
| Recommendation | src/recommendation/recommendation_server.py | `python3 <repo>/modules/hermes/validate_service_lab.py recommendation` | `python3 <repo>/modules/hermes/deploy_service_lab.py recommendation` |
| Quote | src/quote/app/routes.php | `python3 <repo>/modules/hermes/validate_service_lab.py quote` | `python3 <repo>/modules/hermes/deploy_service_lab.py quote` |

Report changed files, test outcomes, deployment evidence and uncertainty in REPAIR-REPORT-<service>.md. Verify fresh telemetry and real request outcomes after deployment. On resolved notifications, verify recovery without redeploying. Do not treat alert resolution or absent errors alone as proof of health.

For availability incidents, read <repo>/modules/availability/README.md. Distinguish an unreachable service from reachable service/missing spans and a missing checker heartbeat. A stopped approved container with healthy source can be restored through its existing fixed helper without a source edit. Configuration changes outside those helpers should be reported as actionable suggestions. Never invent a source defect to explain a telemetry gap.
