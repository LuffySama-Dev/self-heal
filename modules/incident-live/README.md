# Incident Live

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

Native SigNoz dashboard: **Incident Live — Hermes repair lab**, ID `instance-id-011`.
Open it under Dashboards in the existing forwarded SigNoz UI.

Use 20 October 2026, 09:55–10:20 UTC (15:25–15:50 Asia/Calcutta) to view the completed automatic payment drill. Historical events preserve original timestamps; `self_heal.backfilled=true` identifies imports. For the next live drill, select the last 30 minutes and enable dashboard refresh. No new fault was introduced for this dashboard task.

## Evidence

Payment Charge charts use actual lab server spans. No traffic means unknown health, not zero errors. The chronological log evidence includes webhook receipt, SigNoz/Graphify tool responses, successful payment source patches, regression test counts, deployment artifacts, recovery notification receipt and completion of its Hermes session. Expand rows to inspect evidence and incident/session IDs; filter those IDs in Logs Explorer when incidents overlap. Tool responses do not prove successful investigation, and session completion does not independently prove recovery. Compare the recovered traffic and deployment checks.

The adapter exports structured tool summaries, not private reasoning, credentials, arbitrary terminal output or full transcripts. The known payment source patch is included. The current adapter recognizes the Payment, Recommendation and Quote lab source paths and configured lab rules; it is not a generic incident engine. The initial dashboard measurements below were Payment-specific. Source-diff exports need review before expanding to other files.

## Runtime

`bridge.py` reads Hermes SQLite in read-only mode every five seconds. It sends OTLP logs via the existing collector at the configured `otlp_logs_url` endpoint. If Docker reallocates the collector port, update `otlp_logs_url` in local configuration (or `SELF_HEAL_OTLP_LOGS_URL`). It requires no Docker group, sudo or SigNoz admin credential.

User service: `systemctl --user status incident-live`. Stop with `systemctl --user stop incident-live`. Installation copy is `~/.config/systemd/user/incident-live.service`.

Runtime state and API validation evidence: `${PROJECTS_DIR}/incident-live-data/`. Checkpoints advance only after accepted exports; retry after an ambiguous network failure can duplicate events. Stable `self_heal.id` allows deduplication. The adapter heartbeat confirms polling/export activity, not application or Hermes health. Deployment artifacts are correlated to a webhook session by time and an explicit artifact path in its terminal results.

`dashboard.json` is the native v6 dashboard definition. Live instance was created and updated with the SigNoz API using the existing local credential helper; no credentials are saved here.

## Validation (21 October 2026)

Seven parser/export tests passed (`python3 -m unittest discover -s modules/incident-live -v`). All six query panels passed the SigNoz query API with no warnings after explicit resource context selection. Historical results include the 50% error interval, subsequent zero-error traffic, failed/passing regression tests, patch, deployment artifact, recovery receipt and follow-up completion. A current-time query confirms live heartbeat ingestion. Service is active. Browser rendering has not been visually checked.

Official references: [SigNoz list panels](https://signoz.io/docs/dashboards/panel-types/list/), [dashboard management](https://signoz.io/docs/userguide/manage-dashboards/), [OTLP logs](https://signoz.io/docs/logs-management/send-logs-to-signoz/). The installed SigNoz MCP dashboard resource schemas supplied the v6 JSON format.

## Incident counters

The top row contains Total Incident Count, Ongoing Incidents and Resolved Incidents. Counts group by `self_heal.incident` (rule ID plus firing start timestamp), so duplicate deliveries and investigation events do not inflate them. They include incidents overlapping the selected interval, including those already open at its start, and show status as of the selected end. Thus Total = Ongoing + Resolved. Recovery means a resolved webhook was received by Hermes, not merely successful deployment. Notification delays can leave an incident ongoing here after SigNoz itself resolves it.

Only retained adapter evidence is counted. Missing recovery delivery may leave an incident open; expired opening evidence prevents it being counted. These counters are scoped to the lab, not all SigNoz alerts. API validation checked firing `[1,1,0]`, recovered `[1,0,1]`, an incident carried into the window `[1,1,0]`, and an empty window `[0,0,0]`. Results: `${PROJECTS_DIR}/incident-live-data/counters-validation.json`.

## Incident durations

Four timing panels show **seconds for the latest incident overlapping the selected range**, as of its end. They do not average unrelated incidents. Investigation runs from Hermes's firing-message timestamp to the tool-call timestamp of the successful payment source patch. Fix and test runs from that patch call to deployment-helper start. Deployment runs from helper start (including its candidate tests) to `deployed_verified`. Total incident runs from the actual SigNoz payload `startsAt` to `endsAt`; this excludes recovery notification delivery delay and the follow-up session.

These are observable workflow boundaries, not precise measurements of model thinking time. A successful patch is correlated through its tool-call ID. Deployment boundaries are emitted only from a verified result artifact linked to the session. Missing, failed or not-yet-complete milestones show no data instead of zero or an older incident's duration. Payload transitions preserve original event timestamps; historical replay can include facts delivered later, so it is not an as-known-at-the-time audit.

For the 21 October drill, API validation returned investigation 38.152s, fix/test 16.073s, deployment 18s, total alert firing to resolution 420s. Historical unfinished and empty windows returned no durations. Validation: `${PROJECTS_DIR}/incident-live-data/timings-validation.json`. Eight adapter tests pass, including patch correlation, transition timestamps and exclusion of rolled-back deployments. Browser rendering remains unverified by the agent.
