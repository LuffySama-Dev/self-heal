"""SigNoz client; credentials come from environment or GNOME Keyring, never JSON config."""
import json
import os
import subprocess
import urllib.error
import urllib.request
from selfheal_config import SIGNOZ_URL

def credential(env_name, application, account):
    value = os.environ.get(env_name, '').strip()
    if not value:
        env = dict(os.environ, DBUS_SESSION_BUS_ADDRESS=f'unix:path=/run/user/{os.getuid()}/bus')
        result = subprocess.run(['secret-tool','lookup','application',application,'account',account],env=env,text=True,capture_output=True,timeout=15)
        value = result.stdout.strip() if result.returncode == 0 else ''
    if not value or '\n' in value or '\r' in value:
        raise RuntimeError('Required credential is unavailable: ' + env_name)
    return value

def api(path, body=None, method=None):
    if not path.startswith('/api/'):
        raise ValueError('Expected a SigNoz API path')
    key=credential('SIGNOZ_API_KEY','signoz','self-heal-codex')
    req=urllib.request.Request(SIGNOZ_URL.rstrip('/')+path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'SIGNOZ-API-KEY':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            raw=response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        # Error payloads can contain private query data; do not print them.
        raise RuntimeError('SigNoz request failed with HTTP '+str(exc.code)) from None
