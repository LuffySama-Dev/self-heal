"""Shared non-secret configuration. Local paths are relative to the config file."""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get('SELF_HEAL_CONFIG', REPO / '.local/config.json')).expanduser().resolve()
VALUES = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
if not isinstance(VALUES, dict):
    raise ValueError('Configuration must be a JSON object')

def setting(name, default=None):
    return os.environ.get('SELF_HEAL_' + name.upper(), VALUES.get(name, default))

def path(name, default):
    value = Path(os.path.expandvars(str(setting(name, default)))).expanduser()
    return value if value.is_absolute() else CONFIG_PATH.parent / value

PROJECTS = path('projects_dir', REPO.parent)
CHECKOUT = path('checkout_dir', PROJECTS / 'otel-demo-repair-lab')
PAYMENT_DIR = path('payment_dir', PROJECTS / 'payment-repair-drill')
LABS_DIR = path('labs_dir', PROJECTS / 'self-heal-labs')
HERMES_HOME = path('hermes_home', Path.home() / '.hermes')
INCIDENT_STATE = path('incident_state_dir', PROJECTS / 'incident-live-data')
RULES_PATH = path('rules_file', CONFIG_PATH.parent / 'rules.json')
DOCKER_HOST = setting('docker_host', 'unix:///var/run/docker.sock')
NETWORK = setting('docker_network', 'opentelemetry-demo')
IMAGE_PREFIX = setting('image_prefix', 'ghcr.io/open-telemetry/demo:3.1.0-')
OTLP_LOGS_URL = setting('otlp_logs_url', 'http://127.0.0.1:4318/v1/logs')
SIGNOZ_URL = setting('signoz_url', 'http://127.0.0.1:8080')

def rules(group):
    data = json.loads(RULES_PATH.read_text()) if RULES_PATH.exists() else {}
    return data.get(group, {})

def require_rule(service):
    value = rules('symptom').get(service)
    if not value or value.startswith('REPLACE_'):
        raise RuntimeError('Configure the symptom alert rule ID for ' + service)
    return value
