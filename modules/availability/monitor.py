"""Fixed lab probes, independent TCP reachability, and OTLP monitor heartbeat."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import concurrent.futures
import json
import socket
import sys
import time
import urllib.request
sys.path.insert(0, str(config.REPO/'modules/fault-injector'))
import injector
import lab_runtime
TARGETS = {'payment': 50051, 'recommendation': 9001, 'quote': 8090}
ENDPOINT = config.OTLP_LOGS_URL

def check(service):
    name = service + '-repair-lab'
    reachable = False
    detail = 'container unavailable'
    try:
        info = json.loads(lab_runtime.docker('inspect', name).stdout)[0]
        if info['State']['Running']:
            address = info['NetworkSettings']['Networks'][config.NETWORK]['IPAddress']
            with socket.create_connection((address, TARGETS[service]), timeout=3):
                reachable = True
            detail = 'TCP reachable'
    except Exception:
        detail = 'container or TCP unavailable'
    # These real requests produce expected server spans even with no drill running.
    if reachable:
        try:
            rows = injector.probe(name) if service == 'payment' else lab_runtime.probe(lab_runtime.LABS[service])
            detail += '; request observations=' + str(len(rows))
        except Exception:
            detail += '; request probe failed'
    return {'service': name, 'reachable': str(reachable).lower(), 'detail': detail}

def export(rows):
    def attr(k,v): return {'key':k, 'value':{'stringValue':v}}
    records = [{'timeUnixNano':str(time.time_ns()), 'severityText':'INFO', 'body':{'stringValue':r['detail']}, 'attributes':[attr('availability.service',r['service']), attr('availability.reachable',r['reachable'])]} for r in rows]
    body = {'resourceLogs':[{'resource':{'attributes':[attr('service.name','self-heal-availability')]},'scopeLogs':[{'scope':{'name':'lab-availability'},'logRecords':records}]}]}
    req=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as response: result=json.load(response)
    if int(result.get('partialSuccess',{}).get('rejectedLogRecords',0)): raise RuntimeError('Monitor records rejected')

if __name__ == '__main__':
    while True:
        start=time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            rows=list(pool.map(check,TARGETS))
        export(rows)
        print(json.dumps(rows),flush=True)
        time.sleep(max(1,30-(time.monotonic()-start)))
