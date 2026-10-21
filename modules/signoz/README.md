# Using SigNoz self-hosted

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

SigNoz is the selected observability backend. Its installation is separate at `${PROJECTS_DIR}/signoz`; see that directory's README.md for deployment and operating commands. Only usage documentation belongs in this repository.

UI: http://localhost:8081 through an SSH tunnel to your server. SigNoz v0.146.0 uses its own Collector v0.144.14 and ClickHouse/PostgreSQL/Keeper. The demo Collector forwards traces, metrics and logs to `signoz-ingester:4317` over `signoz-network`, without exposing ingestion ports publicly.

Initial admin/organization setup is complete. Verified directly in ClickHouse on 2026-10-20: 16,013 trace spans across 19 services, 31,058 metric samples and 5,942 log records; counts increased between checks. SigNoz and demo UI health checks pass. Both Collectors had no export errors in the final 15-second check. Some telemetry was dropped while the initial setup was pending and the exporter queue filled; fresh data now flows normally. Start SigNoz before the demo because its network must exist first.

Official installation guide: https://signoz.io/docs/install/docker/

## Application dashboard

Prepared dashboard: `OTel Demo — Application Health`, based on the official SigNoz APM Metrics V2 template. JSON resides at `${PROJECTS_DIR}/signoz/dashboards/otel-demo-application-health.json`. All referenced metric names were found in the live SigNoz metrics tables. Created dashboard ID `instance-id-008` through the authenticated V2 API. All eight panel queries return HTTP 200 for environment `default` and service `frontend`; latency, request rate, errors, external calls and operations return data. DB panels are empty for frontend, which has no matching DB-call metrics. Browser rendering has not been inspected.

Open the existing dashboard through Dashboards → OTel Demo — Application Health. Select deployment.environment `default`, a demo service (for example `frontend`), and the desired top-level operations. This environment value is the observed ingestion label, not a declaration that this server is production.

Official template: https://signoz.io/docs/dashboards/dashboard-templates/apm-metrics/
