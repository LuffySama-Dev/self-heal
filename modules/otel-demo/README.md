# Using OpenTelemetry Demo

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

The demo is a separate deployment, not vendored into this repository.

- Checkout: `${PROJECTS_DIR}/opentelemetry-demo`
- Release: `3.1.0`
- Commit: `dedc0178918e260823323b8d95005a8cb924b007`
- Server-local override: `${PROJECTS_DIR}/opentelemetry-demo/compose.local.yaml`

The override binds all published ports to 127.0.0.1 for private access over an SSH tunnel. It is local to the demo checkout and is not tracked by self-heal.

The deployment includes the demo application, its supporting services and OTel Collector. Bundled Grafana, Jaeger, Prometheus, OpenSearch and OpAMP server are excluded. SigNoz self-hosted is installed separately at `${PROJECTS_DIR}/signoz`. The demo Collector forwards to `signoz-ingester:4317` on the external `signoz-network`, configured in `compose.local.yaml` and `otelcol-signoz.yaml`. Start SigNoz before the demo.

From the demo checkout, the Compose configuration is:

```bash
cd ${PROJECTS_DIR}/opentelemetry-demo
docker compose --env-file .env --env-file .env.override \
  -f compose.yaml -f compose.full.yaml \
  -f compose.extras.yaml \
  -f compose.local.yaml config --quiet
```

Demo is running with `DEMO_VERSION=3.1.0` and `IMAGE_VERSION=3.1.0` in its server-local `.env.override`. No Make installation is required. Demo source, images and runtime data do not belong in the self-heal repository.

## Operations

Use the same Compose arguments shown above, replacing `config --quiet` with:

- `ps` to view status.
- `up -d --no-build --wait --wait-timeout 240` to start.
- `stop` to stop without removing containers.

Docker group membership is configured for `<operator>`. Existing sessions may need reconnecting; `sg docker -c 'docker ...'` also runs commands with the new membership. Docker is enabled at boot.

## Browser access

On your own computer, open a tunnel using your server SSH hostname/address:

```bash
ssh -N -L 8080:127.0.0.1:8080 <ssh-user>@<HETZ_HOST>
```

Keep that terminal open. Visit:

- Web store: http://localhost:8080/
- Feature flags: http://localhost:8080/feature
- Load generator: http://localhost:8080/loadgen/

No public inbound demo ports need opening.

## Validation

Validated on 2026-10-20 after removing bundled backends: 23 containers running, all configured healthchecks healthy. Store, feature flags and load generator returned HTTP 200. The Collector is now configured to forward traces, metrics and logs to SigNoz. End-to-end ingestion is verified: fresh demo traces, metrics and logs are stored in SigNoz ClickHouse. Initial SigNoz account setup is complete. The owner subsequently confirmed browser access. Endpoint examples here describe the original deployment; use your own configuration.

Official deployment documentation: https://opentelemetry.io/docs/demo/docker-deployment/
