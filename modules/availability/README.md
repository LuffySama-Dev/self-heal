# Lab availability monitoring

Monitor targets are fixed to payment-repair-lab, recommendation-repair-lab and quote-repair-lab. See [setup](../../SETUP.md) for deployment and credentials.

`monitor.py` checks TCP reachability from the host to the configured Docker network and generates real requests every 30 seconds (6 Payment, 3 Recommendation, 3 Quote). It sends a heartbeat directly to the configured SigNoz OTLP logs endpoint, separately from application traces through the demo Collector. No drill needs to be active for expected spans to exist.

One rule per service fires if no successful reachability probe or no monitor record exists in two minutes, or no expected server spans exist in five minutes. SigNoz evaluates every minute with its additional data delay and notification scheduling. Existing error/latency alerts remain separate.

Filter `self-heal-availability` logs by `availability.service`: false reachability suggests a stopped/unreachable endpoint; reachable probes with absent spans suggest a telemetry gap; absent monitor records suggest checker/ingestion failure. Missing spans do not prove that every telemetry signal is absent. TCP success alone does not prove business correctness.

Create disabled rules with `python3 scripts/configure_alerts.py --group availability --apply`. IDs are written to ignored local configuration. Warm up for at least seven minutes and verify delayed queries are healthy before enabling. Initial development enablement warmed up too briefly and produced startup alerts; these were excluded from the clean outage test.

`validate.py` runs the actual SQL decision against six fixtures and the three live queries; it requires a configured ClickHouse container and Docker access and writes only local ignored evidence. `validation.json` contains the six synthetic case results. `alert-rules.example.json` contains portable, disabled rules. A native SigNoz dashboard is provided by the Incident Live module; its adapter reads availability rule IDs from shared configuration.

Historical live validation: Quote was stopped, its outage alert reached Hermes, the coordinator restored the container, and the real recovery notification reached Hermes. Both sessions completed. This demonstrated alert delivery, not autonomous outage repair. Missing telemetry/checker conditions were validated with SQL fixtures, not separate live outages. Raw session payloads and live rule IDs are not included in the public repository.

A whole-host, SigNoz or delivery-path outage needs an external watchdog. Scheduled probes add baseline traffic and can change measured fault rates. These rules cover only the lab targets, not the entire OTel Demo.

Official reference: https://signoz.io/docs/alerts-management/user-guides/how-to-configure-alerts-for-missing-data/
