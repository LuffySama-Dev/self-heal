"""Hermes command secret source: stdout is consumed only by its credential loader."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import os
import subprocess
os.environ['DBUS_SESSION_BUS_ADDRESS'] = f'unix:path=/run/user/{os.getuid()}/bus'
value = subprocess.check_output(['secret-tool', 'lookup', 'application', 'self-heal-hermes', 'account', 'webhook-signing'], text=True, timeout=15).strip()
if not value or any(c in value for c in '\r\n'):
    raise SystemExit('Missing or invalid signing credential')
print('WEBHOOK_SECRET=' + value)
