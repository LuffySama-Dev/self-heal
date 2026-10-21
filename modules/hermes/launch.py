"""Load service secrets from the user's encrypted keyring, then exec."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import os
from pathlib import Path
import subprocess
import sys

os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{os.getuid()}/bus"


def secret(application, account):
    value = subprocess.check_output(
        ["secret-tool", "lookup", "application", application, "account", account],
        text=True, timeout=15,
    ).strip()
    if not value:
        raise RuntimeError(f"Unlock the keyring: missing {application}/{account}")
    return value


mode = sys.argv[1]
if mode == "gateway":
    import json
    state_file = config.CONFIG_PATH.parent / "maintenance.json"
    if state_file.exists() and json.loads(state_file.read_text()).get("phase") != "active":
        raise SystemExit(78)  # systemd RestartPreventExitStatus; planned maintenance

if mode == "mcp":
    os.environ["SIGNOZ_API_KEY"] = secret("signoz", "self-heal-codex")
    os.environ["SIGNOZ_URL"] = config.SIGNOZ_URL
    os.environ["TRANSPORT_MODE"] = "stdio"
    command = [
        str(config.path('signoz_mcp_bin', config.PROJECTS/'signoz-mcp-server/bin/signoz-mcp-server'))
    ]
elif mode in ("gateway", "relay"):
    os.environ["WEBHOOK_SECRET"] = secret("self-heal-hermes", "webhook-signing")
    if mode == "gateway":
        command = [str(config.path('hermes_bin', Path.home()/'.local/bin/hermes')), "gateway", "run"]
    else:
        os.environ["RELAY_PORT"] = str(config.setting("relay_port",8645))
        os.environ["HERMES_WEBHOOK_URL"] = config.setting("hermes_webhook_url","http://127.0.0.1:8644/webhooks/signoz")
        os.environ["RELAY_TOKEN"] = secret("self-heal-hermes", "signoz-relay")
        os.environ["RELAY_HOST"] = config.setting('relay_host','127.0.0.1')
        command = [sys.executable, os.path.join(os.path.dirname(__file__), "relay.py")]
else:
    raise SystemExit("Expected gateway, relay or mcp")
os.execv(command[0], command)
