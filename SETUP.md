# Setup: isolated self-healing lab

This guide targets Linux with Docker Engine and Python 3.10+. The demonstrated application revision is OTel Demo 3.1.0 (`dedc0178918e260823323b8d95005a8cb924b007`). Existing results used SigNoz 0.146.0, Graphify OSS 0.9.92 and Hermes; model/provider access is configured separately. Product upgrades can change APIs or source anchors. Keep the pinned demo source and image version aligned.

The integration scripts use Python's standard library. Docker Compose, Git, a working Docker connection and (for encrypted credential lookup) `secret-tool` plus an unlocked Secret Service keyring are external prerequisites. OS installation and Docker group changes require the machine owner's privileges. Do not run the whole agent as root.

## 1. Prepare configuration

Run from this repository's root after cloning it. Keep third-party checkouts alongside it, not inside it.

```bash
mkdir -p .local
chmod 700 .local
cp config/config.example.json .local/config.json
chmod 600 .local/config.json
```

Edit `.local/config.json` for your paths, Docker network, SigNoz UI/API URL, host OTLP logs endpoint and executable locations. The example assumes `~/projects`; change it if needed. No credentials belong in this file. Paths expand `~` and environment variables; relative paths resolve against the config file's directory. The default configuration file is `.local/config.json` in this checkout. Set `SELF_HEAL_CONFIG` to use another absolute path. Each setting also accepts `SELF_HEAL_<UPPERCASE_KEY>` as an override, for example `SELF_HEAL_DOCKER_NETWORK`.

`config/rules.example.json` documents the ID schema; the alert creation script generates `.local/rules.json`. Set `rules_file` if the IDs should live elsewhere. Keep container names (`*-repair-lab`), service namespaces and in-container application ports fixed: they define the deployment helpers' target boundaries, not arbitrary production targets.

## 2. Bring up upstream products separately

Follow the products' official installation guides, then check these integration contracts:

- [SigNoz Docker setup](https://signoz.io/docs/install/docker/): complete initial account/organization setup, keep the UI and host ingestion endpoint bound privately, and create a service-account API key with the permissions needed for the lab. Set `signoz_url` and `otlp_logs_url` to your actual published endpoints. The latter is the full `/v1/logs` URL.
- [OTel Demo Docker deployment](https://opentelemetry.io/docs/demo/docker-deployment/): check out the pinned revision above. Run the application/support services and its Collector on the configured Docker network. Disable bundled observability backends if using SigNoz. Configure all three Collector pipelines to export to your SigNoz Collector; preserve any span-metrics connector needed by your dashboards. The repair containers expect `product-catalog:3550` and `otel-collector:4317`/`:4318` on that network. Collector URLs are configurable. Bind demo UI ports to loopback. Verify fresh traces, metrics and logs in SigNoz before proceeding.
- [Hermes documentation](https://hermes-agent.nousresearch.com/docs/): install and authenticate using your own supported model/provider. The recorded runs used GPT-6.1 SOL, medium reasoning. Do not copy another installation's authentication files.
- [Graphify OSS](https://github.com/Graphify-Labs/graphify): install the OSS package outside this repository, index the repair checkout in code-only mode, and configure its stdio MCP server in Hermes. See [module details](modules/graphify/README.md). Check the official CLI help for your installed version.
- [SigNoz MCP](https://github.com/SigNoz/signoz-mcp-server): install separately and set `signoz_mcp_bin` to the actual executable. Configure Hermes to launch `python3 <repo>/modules/hermes/launch.py mcp`. This supplies the URL, API key and stdio transport at runtime.

The upstream deployments are intentionally not vendored or installed by our scripts. Confirm the network names and ports from your deployment, rather than copying historical server values in experiment reports. For remote viewing, forward the actual loopback UI port with SSH using your own username and hostname.

## 3. Prepare the repair checkout and labs

In a separate directory selected by `checkout_dir`:

```bash
git clone https://github.com/open-telemetry/opentelemetry-demo.git ~/projects/otel-demo-repair-lab
git -C ~/projects/otel-demo-repair-lab checkout dedc0178918e260823323b8d95005a8cb924b007
```

Adjust both paths if your configuration differs. Pull the three `ghcr.io/open-telemetry/demo:3.1.0-{payment,recommendation,quote}` images and `ghcr.io/open-feature/flagd:v0.16.0`. The lab setup creates no host port bindings and disables the payment fault/PII feature flags.

From this repository:

```bash
python3 scripts/setup_labs.py
python3 scripts/setup_labs.py --apply
python3 modules/hermes/validate_service_lab.py recommendation
python3 modules/hermes/validate_service_lab.py quote
python3 modules/fault-injector/injector.py check --development --service payment --seed 0
```

The first command is a preflight; `--apply` creates four containers and the required source snapshots, locks and payment fixtures. It refuses to replace existing containers/files. If Docker creation partially fails, inspect the named containers and retained files before retrying; there is no destructive automatic reset. Candidate validation uses disposable containers. The injector's `check` command qualifies a fault but does not deploy it.

Copy [LAB-POLICY.md](config/LAB-POLICY.md) to `MULTISERVICE-LAB.md` in the repair checkout and replace `<repo>` with this repository's absolute path. Preserve the checkout's AGENTS.md. Give Hermes the repository location in its route instructions. Before enabling unattended deployment, review its fixed-target helpers and exact command allowlist. Docker membership gives broad host authority; these helper boundaries are not an OS sandbox.

## 4. Configure credentials and authenticated delivery

Follow the dedicated [Hermes setup walkthrough](docs/HERMES_SETUP.md) for login, credential storage, complete example configuration, MCP checks and delivery verification.

Our default encrypted keyring lookup attributes are:

| Credential | application | account |
|---|---|---|
| SigNoz service-account API key | `signoz` | `self-heal-codex` |
| Relay bearer token | `self-heal-hermes` | `signoz-relay` |
| Hermes webhook HMAC secret | `self-heal-hermes` | `webhook-signing` |

Use your keyring manager to store the values without putting them in Git or shell history. The standalone SigNoz client also accepts `SIGNOZ_API_KEY` supplied by a secret manager. The gateway/relay launcher currently reads its signing and relay secrets from Secret Service. Do not run `keyring_source.py` interactively: its stdout is intended only for the Hermes secret loader.

In Hermes configure a loopback webhook listener on port 8644 and a `signoz` route. Route toolsets must include SigNoz MCP, Graphify MCP, terminal and file tools. Its prompt should direct the agent to the repair checkout and `MULTISERVICE-LAB.md`, distinguish firing/resolved/test events, and include `{__raw__}` for the payload. Configure the documented command secret source:

```yaml
secrets:
  command:
    enabled: true
    command: "/usr/bin/python3 <repo>/modules/hermes/keyring_source.py"
    helper_timeout_seconds: 20
    override_existing: true
```

Set the webhook secret to `${WEBHOOK_SECRET}` in Hermes config. Start Hermes through `python3 <repo>/modules/hermes/launch.py gateway` so its keyring credentials are available. When using Hermes's service manager, use a user-service drop-in for that command and ensure the service has its existing Docker group membership. Do not change the permissions to accept every shell command.

Start the relay using `python3 modules/hermes/launch.py relay`. Select `relay_host` so the SigNoz container can reach it; a loopback default alone is not reachable from a separate container. Bind to the appropriate private Docker bridge address and restrict access to that network. Any firewall changes are machine-specific privileged operations. The Hermes listener itself stays on loopback. Use `hermes_webhook_url` if its local port differs.

Create a SigNoz webhook notification channel named **Self-Heal Hermes**, targeting `http://<private-relay-address>:8645/alerts/signoz`, with bearer authentication matching the keyring relay token and resolved notifications enabled. Never embed its token in exported templates. The relay signs requests to Hermes and deduplicates through request IDs. First send a delivery test and verify Hermes handles it without changing application source.

## 5. Import dashboards and create disabled alerts

Import `modules/incident-live/dashboard.json` through the SigNoz dashboard UI. Review it against your installed SigNoz version. For application health, use the official SigNoz APM template linked in the SigNoz module docs.

Preview and then create the lab alert rules:

```bash
python3 scripts/configure_alerts.py --group symptom
python3 scripts/configure_alerts.py --group symptom --apply
python3 scripts/configure_alerts.py --group availability
python3 scripts/configure_alerts.py --group availability --apply
```

Creation leaves alerts **disabled**, records IDs after each successful creation in ignored local configuration, and skips existing IDs on rerun. An interrupted API response can still require checking the UI for an unrecorded rule before retrying. The six lab templates do not recreate the historical main-demo Payment rule; main-demo automation is outside this deployment scope.

Render the availability checker and evidence adapter services:

```bash
python3 scripts/render_units.py
```

Review `.local/units/`, then copy the two units into `~/.config/systemd/user/`, run `systemctl --user daemon-reload`, and enable/start `self-heal-availability.service` and `incident-live.service`. This is a user service setup, not a root install. The availability service needs Docker access; the adapter only reads Hermes state and exports OTLP logs. If service paths contain spaces, use the rendered quoted units. Validate the units with `systemd-analyze --user verify` on your host before starting them.

Wait at least seven minutes for initial samples and delayed evaluation windows. Confirm every lab is reachable and its server spans appear, then enable the six rules in SigNoz. Confirm healthy/inactive states before running a drill. Alert frequency is one minute with no repeated firing notifications; missing-data windows and SigNoz's evaluation delay still apply.

## 6. Run and observe a drill

```bash
python3 modules/fault-injector/injector.py run --development
```

This chooses among the three lab services. `--service quote --seed 0` selects a reproducible Quote test. `--timeout-minutes` bounds observation; timeout/interruption attempts to restore the baseline. Do not overlap manual rollouts with a running drill. Inspect Incident Live and the private local evidence; check real request outcomes as well as alert state. This is deliberate application disruption, so use only the isolated labs.

For the root-only operator installation, see [injector installation](modules/fault-injector/README.md). Source-checkout development mode is not a blind investigation; the agent can read accessible source and prior reports.

## Validation and known limits

`python3 scripts/test.py` runs unit tests without Docker, credentials, upstream checkouts or a live SigNoz instance. `python3 scripts/publication_check.py` reviews the proposed public Git file set and reachable history for known secret/private-data patterns. Neither is proof that all possible secrets have been found. `modules/availability/validate.py` is an optional live ClickHouse test; configure its container name and run with working Docker permissions. It writes only ignored local output.

Portable imports, unit tests, generated service units and public-file checks are tested here. A fresh full installation on a second host has not yet been performed. External products, account setup, keyring unlocking, network wiring and Hermes permissions remain explicit operator steps. Simulithic is coming soon and is not part of setup; do not install or configure it. Do not use the lab results as evidence of production readiness.
