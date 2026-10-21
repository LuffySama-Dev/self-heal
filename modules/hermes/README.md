# Hermes alert investigation

For a new installation, follow the [Hermes setup walkthrough](../../docs/HERMES_SETUP.md) and [portable configuration example](../../config/hermes.example.yaml).

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

## Scope

SigNoz → private authenticated relay → Hermes webhook → SigNoz MCP and local code tools.
Reports currently go to Hermes logs. The approved Payment Charge error alert
is connected; Slack/Telegram delivery, code changes and production deployment
are separate steps.

## Installed on your server

- Hermes v0.22.2: `${PROJECTS_DIR}/hermes-agent`, launcher
  `${HOME}/.local/bin/hermes`. Official stable installer; browser and
  computer-use downloads skipped. No sudo commands were executed by the agent.
- SigNoz MCP v0.15.0: `${PROJECTS_DIR}/signoz-mcp-server`.
  Official Linux binary verified against the release SHA-256 checksum.
- Hermes configuration: `${HOME}/.hermes/config.yaml`.
  Provider `openai-codex`, model `gpt-6.1-sol`, medium reasoning, 20-turn limit.
  User completed a separate Hermes OAuth login. Hermes manages its own OAuth
  credentials; these are not the webhook secrets stored in GNOME Keyring.
- User services: `hermes-gateway` and `self-heal-alert-relay`; linger was already enabled.
- SigNoz notification channel: `Self-Heal Hermes`,
  ID `instance-id-004`.
- Alert: `OTel Demo - Payment Charge error rate above 20%`,
  ID `instance-id-005`.

Hermes source and runtime dependencies are outside this repository. This module
contains only integration code, tests, and documentation.

## Network and authentication

The relay binds to `<relay-bind-address>:8645`, the current `signoz-network` Docker bridge
gateway, at `/alerts/signoz`. Hermes binds only to `127.0.0.1:8644`, route
`/webhooks/signoz`. Neither listener binds to the public host address.

SigNoz sends a Bearer token to the relay. The relay validates it, validates the
JSON envelope, then forwards the unchanged body with Hermes HMAC-V2 headers.
Identical bodies use the same request ID for Hermes's one-hour deduplication.
Upstream errors return 502 rather than acknowledging a lost delivery.
This is a small synchronous relay, not a durable queue.

`launch.py` retrieves secrets from GNOME Keyring over the user's D-Bus:

- `application=self-heal-hermes account=signoz-relay`
- `application=self-heal-hermes account=webhook-signing`
- Existing `application=signoz account=self-heal-codex` for MCP.

Secrets are passed in process memory/environment, not saved in this repository.
SigNoz also holds the relay token in its notification-channel configuration.
After a reboot, the user's encrypted keyring must be unlocked before services
can retrieve secrets. Then restart both user services. Unattended reboot recovery
has not yet been configured or tested.

The firewall rule applied by the user is:

```sh
sudo ufw allow in on br-bfa2e34c659d from <docker-subnet> to <relay-bind-address> port 8645 proto tcp comment 'SigNoz to Hermes relay'
```

If the Docker network is recreated, recheck its bridge name, subnet and gateway
before updating the rule, launcher and SigNoz channel URL.

## Operation

```sh
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
systemctl --user status hermes-gateway self-heal-alert-relay
systemctl --user restart hermes-gateway self-heal-alert-relay
curl http://127.0.0.1:8644/health
```

Hermes reports: `${HOME}/.hermes/logs/gateway.log` and saved sessions.
Relay status: `journalctl --user -u self-heal-alert-relay`.
Stop processing: `systemctl --user stop self-heal-alert-relay hermes-gateway`.

On 20 October 2026, the user authorized expanded access for code repair.
The existing SigNoz credential has the `signoz-admin` role. Hermes now exposes
all 43 tools supplied by the installed SigNoz MCP server, including management
operations, plus the `terminal` and `file` toolsets on the authenticated SigNoz
route. The gateway was restarted and its health endpoint verified.

Local tools run as `<operator>`; no sudo policy or OS privileges were changed.
The repair checkout is `${PROJECTS_DIR}/otel-demo-repair-lab`, branch
`self-heal/payment-code-drill`, separate from the running demo checkout.
Hermes may prepare patches and run local regression tests there. Its route
instructions require review before applying changes to the running deployment,
reserve sudo for the user, and prohibit hiding failures by changing alert rules
or feature flags. These are agent instructions, not a filesystem sandbox:
local tools retain the existing permissions of `<operator>`.

Automatic skill curation remains disabled. Telemetry is treated as untrusted
data. The previous configuration is backed up locally at
`${HOME}/.hermes/config.before-repair-access.yaml` (mode 0600).
The earlier payment drill below used read-only tools; expanded access alone
has not yet demonstrated a successful code repair.

## Validation

```sh
python3 -m unittest discover -s ${PROJECTS_DIR}/self-heal/modules/hermes -p 'test_*.py'
```

Tests verify rejection of invalid authentication/JSON, HMAC-V2 delivery,
stable retry IDs, payload preservation and propagation of upstream failure.
Live local delivery returned HTTP 202 and Hermes completed a Codex inference
turn, called `signoz_list_services`, and confirmed MCP connectivity.
After the user applied the firewall rule, the SigNoz notification-channel test
returned HTTP 204. The relay received the request and Hermes accepted it with
HTTP 202, called `signoz_list_services`, and completed a response in 13.1 seconds.
Verified on 2026-10-20 at 11:12 IST. This verifies notification delivery and MCP
connectivity. The subsequent payment failure exercise is recorded separately
in `payment-drill.md`.

## Payment alert

The saved rule and query are in `${PROJECTS_DIR}/signoz/alerts/`.
The query counts PaymentService/Charge server spans from namespace
`opentelemetry-demo`. It evaluates the trailing five-minute error rate at three
points one minute apart, requiring each point to exceed 20% and have at least
five requests. SigNoz uses `all_the_times`, a two-minute evaluation range,
three required points and one-minute evaluation frequency. The installed
version has no separate configurable pending duration.

The evaluator also applies its existing two-minute data delay, and notification
grouping adds delivery latency. Recovery occurs when the sustained condition
no longer holds. Fewer than five requests returns zero; this rule does not
detect missing traffic or a complete absence of payment requests.

`deployment.environment=default` exists on generated metrics but is absent from
the payment span resources; the trace alert therefore filters on the observed
`service.namespace` value instead. Compare historical notifications with the
exact query window, not a fresh five-minute window ending at delivery time.

## Official references

- https://hermes-agent.nousresearch.com/docs/getting-started/installation
- https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/
- https://hermes-agent.nousresearch.com/docs/reference/cli-commands
- https://signoz.io/docs/alerts-management/notification-channel/webhook/
- https://signoz.io/docs/alerts-management/migrate-notification-channel-api-v1-to-v2/
- https://github.com/SigNoz/signoz-mcp-server

## Automatic lab deployment update

The later user authorization replaces the per-fix approval requirement for payment-repair-lab only. Docker group access and the exact pre-authorized deployment helper have been verified through a real Hermes webhook run. See [automatic lab deployment](automatic-lab-deployment.md) for tests, rollback behavior and scope. Earlier trial restrictions above describe historical setup.

### Gateway profile credential loading (21 October)
The current Hermes gateway resolves secrets through profile scopes. `secrets.command` uses `keyring_source.py` to load WEBHOOK_SECRET from GNOME Keyring into that scope; inherited launcher environment alone was insufficient after restart. The webhook config references `${WEBHOOK_SECRET}`. Credentials are not written into config or this repository. Multiplex mode remains enabled; no standalone override is used.
