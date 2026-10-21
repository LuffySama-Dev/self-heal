"""Evaluate actual ClickHouse rule SQL against normal and missing-data cases."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import json,subprocess
from pathlib import Path
from configure import query

def sql(q):
 r=subprocess.run(['sg','docker','-c','docker exec -i '+__import__('shlex').quote(config.setting('clickhouse_container','signoz-clickhouse'))+' clickhouse-client'],input=q,text=True,capture_output=True,check=True)
 return r.stdout.strip()

results=[]
# Replace inputs, preserve exactly the deployed decision SELECT.
decision=query('quote').split('SELECT evaluation_end AS ts,',1)[1]
for label,samples,reachable,spans,expected in [('healthy',4,4,30,0),('service_down',4,0,10,1),('telemetry_missing',4,4,0,1),('monitor_missing',0,0,30,1),('everything_missing',0,0,0,1),('brief_failed_probe',4,3,30,0)]:
 q=f'WITH probes AS (SELECT {samples} samples,{reachable} reachable), traces AS (SELECT {spans} spans) SELECT '+decision
 actual=int(float(sql(q)));assert actual==expected,(label,actual)
 results.append({'case':label,'value':actual,'expected':expected})
for service in ['payment','recommendation','quote']:
 value=sql(query(service).replace('{{.end_datetime}}','now64(3)'))
 assert value.endswith('\t0'),(service,value)
 results.append({'service':service,'live_query':value})
(config.CONFIG_PATH.parent/'availability-validation.json').write_text(json.dumps(results,indent=2));print('PASS: six missing-data cases and three healthy live queries')
