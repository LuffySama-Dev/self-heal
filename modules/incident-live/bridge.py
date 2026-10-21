"""Read-only Hermes evidence -> OTLP logs. No agent reasoning or raw tool output exported."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import urllib.request

ROOT = config.PROJECTS
RULE = config.rules('symptom').get('payment','unconfigured-payment-rule')
SERVICE = 'self-heal-incident-live'
RULES = {RULE: 'payment-repair-lab', **{v:k+'-repair-lab' for k,v in config.rules('symptom').items()}}

RULES.update({v:k+'-repair-lab' for k,v in config.rules('availability').items()})

def decode(value):
    try:
        return json.loads(value or '{}')
    except (ValueError, TypeError):
        return {}

def notification(content):
    marker = 'Notification payload:'
    if marker not in (content or ''):
        return None
    try:
        payload = json.JSONDecoder().raw_decode(content.split(marker, 1)[1].lstrip())[0]
    except ValueError:
        return None
    for alert in payload.get('alerts', []):
        if alert.get('labels', {}).get('ruleId') in RULES:
            return alert

def event(key, timestamp, stage, body, session='', incident=''):
    return dict(id=hashlib.sha256(key.encode()).hexdigest(), timestamp=timestamp,
                stage=stage, body=body, session=session, incident=incident)

def evidence(row, incident):
    key, session, role, content, tool, timestamp = row
    prefix = f'message:{key}'
    if role == 'user':
        alert = notification(content)
        if alert:
            resolved = alert.get('status') == 'resolved'
            return event(prefix, timestamp, 'recovery_received' if resolved else 'alert_received',
                         'Hermes received SigNoz RESOLVED notification' if resolved else 'Hermes received SigNoz FIRING notification', session, incident)
    if role != 'tool':
        return None
    result = decode(content)
    stage, body = '', ''
    if tool and (tool.startswith('mcp__signoz__') or tool.startswith('mcp__graphify__')):
        stage, body = 'investigating', f'Tool response recorded: {tool} (inspect Hermes evidence for query outcome)'
    elif tool == 'patch' and result.get('success') is True:
        diff = result.get('diff', '').replace('\\n', '\n')
        # Only the known lab source is eligible; reports and arbitrary files are excluded.
        if re.match(r'--- a/(?:' + re.escape(str(config.CHECKOUT)) + r'/)?(?:src/payment/charge\.js|src/recommendation/recommendation_server\.py|src/quote/app/routes\.php)\n', diff):
            stage, body = 'fix_applied', 'Service source patch succeeded:\n' + diff[:6000]
    elif tool == 'terminal':
        output = result.get('output', '').replace('\\n', '\n')
        counts = re.findall(r'(?:#|ℹ) (?:tests|pass|fail) \d+', output)
        if counts:
            stage, body = 'tests', 'Regression test output: ' + '; '.join(counts) + f'; command exit code: {result.get("exit_code")}'
        for line in output.splitlines():
            probe = decode(line)
            if isinstance(probe, dict) and isinstance(probe.get('calls'), int) and isinstance(probe.get('failures'), int) and isinstance(probe.get('rows'), list):
                stage, body = 'tests', f"Independent candidate acceptance checks: {probe['calls']} calls, {probe['failures']} failures; command exit code: {result.get('exit_code')}"
        if result.get('status') == 'blocked':
            stage, body = 'blocked', 'Hermes terminal action blocked by execution policy; no execution confirmed.'
    if stage:
        return event(prefix, timestamp, stage, body, session, incident)

def collect(database):
    events, windows = [], []
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as con:
        sessions = con.execute("select id,started_at,ended_at,end_reason from sessions where source='webhook'").fetchall()
        for session, started, ended, end_reason in sessions:
            rows = con.execute('select id,session_id,role,content,tool_name,timestamp from messages where session_id=? order by id', (session,)).fetchall()
            alerts = [notification(r[3]) for r in rows if r[2] == 'user']
            alert = next((a for a in alerts if a), None)
            if not alert:
                continue
            incident = alert['labels']['ruleId'] + ':' + alert['startsAt']
            for field, stage in [('startsAt', 'alert_fired'), ('endsAt', 'alert_resolved')]:
                value = alert.get(field, '')
                if value and not value.startswith('0001-'):
                    when = dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
                    events.append(event(stage + ':' + incident, when, stage,
                                        'SigNoz ' + field + ' from the delivered alert payload', session, incident))
            calls = {}
            for calls_json, called_at in con.execute('select tool_calls,timestamp from messages where session_id=? and tool_calls is not null', (session,)):
                for call in decode(calls_json):
                    if call.get('function', {}).get('name') == 'patch':
                        calls[call.get('id') or call.get('call_id')] = called_at
            windows.append((started, ended or time.time(), session, incident, '\n'.join(r[3] or '' for r in rows if r[2] == 'tool' and r[4] == 'terminal')))
            if ended and end_reason == 'webhook_complete' and alert.get('status') == 'resolved':
                events.append(event('followup:' + session, ended, 'recovery_followup_complete', 'Hermes finished processing the recovery notification. Inspect telemetry charts and the local Hermes report for its conclusions.', session, incident))
            for row in rows:
                item = evidence(row, incident)
                if item:
                    events.append(item)
                    if item['stage'] == 'fix_applied':
                        call_id = con.execute('select tool_call_id from messages where id=?', (row[0],)).fetchone()[0]
                        if call_id in calls:
                            events.append(event('repair-start:' + str(row[0]), calls[call_id], 'repair_started',
                                                'Hermes started the source patch that subsequently succeeded; investigation boundary.', session, incident))
    paths = list((config.PAYMENT_DIR / 'deployments').glob('*/result.json')) + list(config.LABS_DIR.glob('*/deployments/*/result.json'))
    for path in paths:
        try:
            result = json.loads(path.read_text())
            finished = dt.datetime.fromisoformat(result['finished_at'].replace('Z', '+00:00')).timestamp()
        except (ValueError, KeyError):
            continue
        matches = [w for w in windows if w[0] <= finished <= w[1] and str(path.parent) in w[4] and RULES.get(w[3].split(':')[0]) == result.get('container')]
        if not matches or result.get('container') not in RULES.values():
            continue
        _, _, session, incident, _ = max(matches)
        status = result.get('status', 'unknown')
        if status == 'deployed_verified':
            begun = dt.datetime.strptime(result['started_at'], '%Y%m%dT%H%M%SZ').replace(tzinfo=dt.timezone.utc).timestamp()
            events.append(event('deploy-start:' + str(path), begun, 'deployment_started',
                                'Deployment helper started (includes candidate tests and live checks).', session, incident))
            events.append(event('deploy-verified:' + str(path), finished, 'deployment_verified',
                                'Deployment helper confirmed deployed_verified.', session, incident))
        events.append(event('deployment:' + str(path), finished, 'deployment',
            f'Lab deployment artifact: {status}; SHA256 {result.get("sha256", "unknown")}; live checks: {json.dumps(result.get("live_checks", []))}. Evidence: {path}', session, incident))
    return sorted(events, key=lambda e: e['timestamp'])

def export(events, endpoint, live_since):
    def attr(k, v):
        return {'key': k, 'value': {'stringValue': str(v)}}
    records = []
    for e in events:
        records.append({'timeUnixNano': str(int(e['timestamp'] * 1e9)),
          'observedTimeUnixNano': str(time.time_ns()), 'severityText': 'INFO',
          'body': {'stringValue': e['body']}, 'attributes': [attr('self_heal.' + k, e[k]) for k in ('id', 'stage', 'session', 'incident')] +
          [attr('self_heal.backfilled', str(e['timestamp'] < live_since).lower()), attr('self_heal.service', RULES.get(e['incident'].split(':')[0], ''))]})
    body = {'resourceLogs': [{'resource': {'attributes': [attr('service.name', SERVICE), attr('service.namespace', 'self-heal-repair-lab')]},
            'scopeLogs': [{'scope': {'name': 'incident-live'}, 'logRecords': records}]}]}
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.load(response)
    if int(result.get('partialSuccess', {}).get('rejectedLogRecords', 0)):
        raise RuntimeError('OTLP rejected records; checkpoint not advanced')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    state_dir = config.INCIDENT_STATE
    state_dir.mkdir(parents=True, exist_ok=True)
    os.umask(0o077)
    with sqlite3.connect(state_dir / 'state.sqlite3') as state:
        state.execute('create table if not exists sent (id text primary key)')
        state.execute('create table if not exists metadata (key text primary key, value real)')
        state.execute('insert or ignore into metadata values (?, ?)', ('live_since', time.time()))
        state.commit()
        live_since = state.execute('select value from metadata where key=?', ('live_since',)).fetchone()[0]
        while True:
            try:
                events = collect(config.HERMES_HOME / 'state.db')
                now = time.time()
                events.append(event(f'heartbeat:{int(now)//60}', now, 'heartbeat', 'Incident Live adapter is polling Hermes evidence; this is not an application health signal.'))
                sent = {r[0] for r in state.execute('select id from sent')}
                pending = [e for e in events if e['id'] not in sent]
                for offset in range(0, len(pending), 100):
                    batch = pending[offset:offset+100]
                    export(batch, os.environ.get('OTLP_LOGS_URL', config.OTLP_LOGS_URL), live_since)
                    state.executemany('insert or ignore into sent values (?)', [(e['id'],) for e in batch])
                    state.commit()
                if pending:
                    print(f'Exported {len(pending)} evidence events', flush=True)
            except Exception as exc:
                print(f'Export failed: {type(exc).__name__}; retrying without advancing checkpoint', flush=True)
                if args.once:
                    raise
            if args.once:
                break
            time.sleep(5)

if __name__ == '__main__':
    main()
