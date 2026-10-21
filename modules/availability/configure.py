"""Create fixed lab availability rules; run from the coordinator's configured environment."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import copy,json,sys
from pathlib import Path
from selfheal_api import api
ROOT=Path(__file__).parent

def query(service):
 return """WITH {{.end_datetime}} AS evaluation_end,
probes AS (SELECT count() AS samples, countIf(attributes_string['availability.reachable']='true') AS reachable
 FROM signoz_logs.distributed_logs_v2
 WHERE resource_fingerprint GLOBAL IN (SELECT fingerprint FROM signoz_logs.distributed_logs_v2_resource WHERE simpleJSONExtractString(labels,'service.name')='self-heal-availability')
 AND attributes_string['availability.service']='SERVICE'
 AND timestamp >= toUnixTimestamp64Nano(toDateTime64(evaluation_end,9)-INTERVAL 2 MINUTE)
 AND timestamp < toUnixTimestamp64Nano(toDateTime64(evaluation_end,9))),
traces AS (SELECT count() AS spans FROM signoz_traces.signoz_index_v3
 WHERE serviceName='SERVICE' AND kind=2 AND resources_string['service.namespace']='self-heal-repair-lab'
 AND timestamp>=evaluation_end-INTERVAL 5 MINUTE AND timestamp<evaluation_end)
SELECT evaluation_end AS ts, toFloat64(samples=0 OR reachable=0 OR spans=0) AS value FROM probes CROSS JOIN traces
""".replace('SERVICE',service+'-repair-lab')

if __name__=='__main__':
 import runpy
 _sys.argv=[str(config.REPO/'scripts/configure_alerts.py'),'--group','availability',*_sys.argv[1:]]
 runpy.run_path(_sys.argv[0],run_name='__main__')
