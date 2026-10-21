# Hermes setup walkthrough

Complete sections 1–3 of [SETUP.md](../SETUP.md) first. Hermes, SigNoz MCP and Graphify are separate installations; this repository supplies their integration. Use the same non-root Linux account for Hermes, the encrypted keyring and the user services. Its Docker access must already work. No credentials or live configuration should be committed.

## Install and authenticate

Follow the [official Hermes installation guide](https://hermes-agent.nousresearch.com/docs/). Check `hermes --help` after installation and set `hermes_bin` in the local project configuration to its executable. For the provider used in our demonstration:

```bash
hermes auth add openai-codex --type oauth --no-browser
```

Complete the displayed login in your normal browser. Keep the device code and generated credentials private. Use `hermes model` to select a model your account supports. Our recorded runs used GPT-6.1 SOL with medium reasoning; this is a description of the experiment, not a guarantee of account availability. Confirm a simple interactive conversation works before adding automation.

## Store the three integration credentials

An unlocked Secret Service keyring and a working user D-Bus session are prerequisites. This guide does not create or unlock a keyring. SigNoz supplies its service-account API key; generate separate random values for the relay bearer token and webhook HMAC secret in your password manager.

Run the following Bash function in a private terminal. It hides input and passes the value through stdin rather than a command argument. Do not enable shell tracing (`set -x`).

```bash
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
store_self_heal_secret() {
  local integration_secret
  read -r -s -p "Paste credential for $1/$2: " integration_secret
  printf '\n'
  if [ -z "$integration_secret" ]; then
    printf 'Empty credential rejected\n' >&2
    return 1
  fi
  printf '%s' "$integration_secret" | secret-tool store \
    --label="Self-Heal $1/$2" application "$1" account "$2"
  local store_status=$?
  unset integration_secret
  return "$store_status"
}
store_self_heal_secret signoz self-heal-codex
store_self_heal_secret self-heal-hermes signoz-relay
store_self_heal_secret self-heal-hermes webhook-signing
unset -f store_self_heal_secret
```

The two relay endpoints must use the same respective values: SigNoz's channel uses the relay bearer token; Hermes and the signing relay share the HMAC secret. Neither value belongs in the public YAML. An unattended service cannot unlock your keyring for you; establish the host's unlock procedure and test it after reboot.

## Configure tools, route and deployment permission

Merge [hermes.example.yaml](../config/hermes.example.yaml) into `~/.hermes/config.yaml` with `hermes config edit`. Preserve existing unrelated settings and avoid duplicate YAML keys. Replace `<repo>`, `<checkout>`, `<graphify-python>` and `<graph-json>` with absolute paths. The Graphify Python executable must be from its installed environment; the graph must index the actual repair checkout. See the [Graphify module](../modules/graphify/README.md).

For paths containing spaces, shell command strings in `secrets.command` and `command_allowlist` require shell quoting around paths; list-valued MCP `args` do not. The allowlist must match the commands the agent actually runs. Copy and customize [LAB-POLICY.md](../config/LAB-POLICY.md) as described in SETUP.md, using the same command spelling and quoting.

The example enables only the five validation/deployment helper commands for unattended execution. It does not grant sudo or disable all command approvals. Hermes still has the authority of its Linux account, including Docker access; this policy is not host isolation. Review the [official approval documentation](https://hermes-agent.nousresearch.com/docs/user-guide/security/) when adapting it.

Check tool connectivity:

```bash
hermes mcp test signoz
hermes mcp test graphify
```

If either fails, fix the executable path, keyring unlock, endpoint or graph path before enabling alerts. The SigNoz launcher supplies the API key at runtime. The command secret source supplies the webhook secret; do not invoke that helper yourself because its output is a credential.

## Start and verify delivery

From this repository, start the gateway in one terminal and relay in another:

```bash
python3 modules/hermes/launch.py gateway
```

```bash
python3 modules/hermes/launch.py relay
```

Check the local Hermes listener with `curl --fail http://127.0.0.1:8644/health`. A healthy listener is only a connectivity check. Use SETUP.md section 4 to configure the private relay binding, firewall and SigNoz notification channel. Send the channel's test notification and inspect Hermes output for its receipt and acknowledgement. Ensure that a test event does not trigger application changes.

For persistence, follow the [official gateway guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/). If a Hermes user service already exists, override its ExecStart to use this project's gateway launcher instead of starting a second gateway. A separate user service can run the relay launcher. Set absolute executable paths and `SELF_HEAL_CONFIG` when using a nondefault configuration path; use the same unlocked keyring account. Check service logs and delivery again after restarting. Machine-specific boot/session configuration may require administrator action.

Proceed with disabled alert creation, Incident Live services and the healthy-baseline checks in SETUP.md. Only then enable the lab rules and start a deliberate drill. Verify the full chain: firing alert, Hermes receipt, investigation, tests, deployment, successful application requests, resolved notification and Hermes recovery confirmation. A successful webhook POST by itself does not establish that a repair succeeded.

## Troubleshooting

| Symptom | Check |
|---|---|
| Launcher reports missing credential | Correct Linux account, unlocked keyring, D-Bus session and the exact credential attributes above. |
| SigNoz cannot reach the relay | Container-to-host route, private bridge binding and firewall; host loopback is not container loopback. |
| Relay rejects a notification | SigNoz bearer token matches the stored relay token. |
| Hermes rejects the signed request | Both processes loaded the same HMAC secret; restart after rotating it. |
| MCP tools are missing | MCP tests, absolute executable paths and route toolsets. |
| Deployment waits for approval | Exact command spelling/quoting and allowlist loaded after gateway restart; do not enable blanket approval bypass. |
| Agent says recovered but dashboard has no recovery | Check the resolved-notification setting, live requests, telemetry and evidence adapter logs independently. |

Product configuration references: [webhooks](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks/) and [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/). This walkthrough has been checked against the installed product source and the working lab configuration; a fresh installation on another host remains to be tested.
