"""Fixed recommendation/quote lab targets, probes, candidate validation and deployment."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

BASE=config.PROJECTS
CHECKOUT=config.CHECKOUT
DATA=config.LABS_DIR
LABS={
 'recommendation':{'file':'src/recommendation/recommendation_server.py','dest':'/app/recommendation_server.py','env':{'FLAGD_HOST':'flagd-repair-lab','FLAGD_PORT':'8013','PRODUCT_CATALOG_ADDR':'product-catalog:3550','RECOMMENDATION_PORT':'9001','PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION':'python','OTEL_PYTHON_LOG_CORRELATION':'true','OTEL_EXPORTER_OTLP_ENDPOINT':config.setting('collector_grpc_url','http://otel-collector:4317')}},
 'quote':{'file':'src/quote/app/routes.php','dest':'/var/www/app/routes.php','env':{'QUOTE_PORT':'8090','IPV6_ENABLED':'false','OTEL_PHP_AUTOLOAD_ENABLED':'true','OTEL_EXPORTER_OTLP_ENDPOINT':config.setting('collector_http_url','http://otel-collector:4318')}},
}
for key,s in LABS.items():
 s.update(name=key,container=key+'-repair-lab',image=config.IMAGE_PREFIX+key)
 s['source']=CHECKOUT/s['file'];s['directory']=DATA/key;s['running']=s['directory']/Path(s['file']).name

def docker(*args,check=True,timeout=90):
 env={k:v for k,v in os.environ.items() if k not in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
 p=subprocess.run(['docker','--host',config.DOCKER_HOST,*args],text=True,capture_output=True,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('Docker failed: '+p.stderr[-1500:])
 return p

def start_container(s,name,path,telemetry=True):
 env={**s['env'],'OTEL_SERVICE_NAME':s['container'] if telemetry else 'candidate-probe','OTEL_RESOURCE_ATTRIBUTES':'service.namespace=self-heal-repair-lab','OTEL_METRIC_EXPORT_INTERVAL':'10000'}
 if not telemetry:env.update(OTEL_SDK_DISABLED='true',OTEL_EXPORTER_OTLP_ENDPOINT='http://127.0.0.1:9',OTEL_EXPORTER_OTLP_TIMEOUT='1',OTEL_PHP_AUTOLOAD_ENABLED='false')
 args=['run','-d','--name',name,'--network',config.NETWORK,'--mount',f'type=bind,src={path},dst={s["dest"]},readonly']
 for key,value in env.items():args+=['-e',key+'='+value]
 return docker(*args,s['image']).stdout.strip()

REC_PROBE='''import json,time,datetime,grpc,demo_pb2 as pb,demo_pb2_grpc as rpc
catalog=rpc.ProductCatalogServiceStub(grpc.insecure_channel("product-catalog:3550"))
ids=[p.id for p in catalog.ListProducts(pb.Empty(),timeout=4).products]
client=rpc.RecommendationServiceStub(grpc.insecure_channel("127.0.0.1:9001"))
for excluded in [[],ids,ids[:-1]]:
 start=time.monotonic();result={"case":"exclude-"+str(len(excluded))}
 try:
  response=client.ListRecommendations(pb.ListRecommendationsRequest(user_id="fault-lab",product_ids=[",".join(excluded)] if excluded else []),timeout=5)
  got=list(response.product_ids)
  result.update(ok=len(got)==min(5,len(set(ids)-set(excluded))) and len(got)==len(set(got)) and not set(got)&set(excluded) and set(got)<=set(ids),rpc_ok=True)
 except Exception as e:result.update(ok=False,rpc_ok=False,message=str(e)[:250])
 result.update(elapsed_s=time.monotonic()-start,time=datetime.datetime.now(datetime.timezone.utc).isoformat())
 print(json.dumps(result))
'''
QUOTE_PROBE='''foreach ([0,1,3] as $n) { $start=microtime(true); $ctx=stream_context_create(['http'=>['method'=>'POST','header'=>"Content-Type: application/json\\r\\n",'content'=>json_encode(['numberOfItems'=>$n]),'ignore_errors'=>true,'timeout'=>5]]); $body=@file_get_contents('http://127.0.0.1:8090/getquote',false,$ctx); $headers=$http_response_header??[]; $status=preg_match('/ 200 /',$headers[0]??'')===1; $value=json_decode($body===false?'null':$body,true); echo json_encode(['case'=>'items-'.$n,'rpc_ok'=>$status,'ok'=>$status && is_numeric($value) && abs($value-round(8.99*$n,2))<0.001,'elapsed_s'=>microtime(true)-$start,'time'=>gmdate('Y-m-d\\TH:i:s\\Z')])."\\n"; }'''

def probe(s,name=None):
 name=name or s['container']
 args=['/venv/bin/python','-c',REC_PROBE] if s['name']=='recommendation' else ['php','-r',QUOTE_PROBE]
 p=docker('exec',name,*args,check=False,timeout=30)
 try:rows=[json.loads(l) for l in p.stdout.splitlines() if l.startswith('{')]
 except ValueError:return []
 if p.returncode or len(rows)!=3:return []
 for r in rows:r['ok']=r['ok'] and r['elapsed_s']<1.0
 return rows

def syntax(s,path):
 if s['name']=='recommendation':
  args=['--entrypoint','/venv/bin/python',s['image'],'-c','import ast; ast.parse(open("/candidate/source").read())']
 else:args=['--entrypoint','php',s['image'],'-l','/candidate/source']
 docker('run','--rm','--network','none','-v',f'{path}:/candidate/source:ro',*args)

def qualify(s,stage,source,expected_failure=False):
 stage.mkdir(parents=True,exist_ok=True);stage.chmod(0o755)
 path=stage/'source';path.write_text(source);path.chmod(0o644)
 syntax(s,path)
 name='fault-probe-'+secrets.token_hex(6)
 try:
  start_container(s,name,path,False)
  for _ in range(15):
   time.sleep(1);rows=probe(s,name)
   if rows and any(r['rpc_ok'] for r in rows):break
  # Quote error mutations can fail all application requests while the HTTP server is running.
  if not rows:raise RuntimeError('No complete candidate probe result')
  if s['name']=='recommendation' and any('connect' in r.get('message','').lower() for r in rows):raise RuntimeError('Candidate failed startup/dependency connection')
  if s['name']=='quote' and not any(r['rpc_ok'] for r in rows):
   check=docker('exec',name,'php','-r',"$s=@fsockopen('127.0.0.1',8090); exit($s?0:1);",check=False)
   if check.returncode:raise RuntimeError('Candidate HTTP server did not start')
  failed=sum(not r['ok'] for r in rows)
  if (expected_failure and not failed) or (not expected_failure and failed):raise RuntimeError('Candidate behavior did not meet qualification requirement')
  return {'calls':len(rows),'failures':failed,'rows':rows}
 finally:docker('rm','-f',name,check=False)

def preflight(s):
 info=json.loads(docker('inspect',s['container']).stdout)[0]
 mounts={m['Destination']:m['Source'] for m in info['Mounts']}
 if info['Config']['Image']!=s['image'] or mounts.get(s['dest'])!=str(s['running']) or not info['State']['Running']:raise RuntimeError('Unexpected lab target/image/mount')
 rows=probe(s)
 if not rows or not all(r['ok'] for r in rows):raise RuntimeError('Lab is not healthy')

def install(s,data,checkout=False):
 docker('stop','-t','3',s['container'])
 if checkout:s['source'].write_bytes(data)
 s['running'].write_bytes(data)
 docker('start',s['container'])

def verify(s):
 for _ in range(12):
  time.sleep(1);rows=probe(s)
  if rows and all(r['ok'] for r in rows):return rows
 raise RuntimeError('Live lab verification failed')

def deploy(name):
 s=LABS[name]
 with (s['directory']/'deploy.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
  work=s['directory']/'deployments'/stamp;work.mkdir(parents=True)
  candidate=s['source'].read_bytes();old=s['running'].read_bytes()
  (work/'previous-source').write_bytes(old);(work/'candidate-source').write_bytes(candidate)
  r={'container':s['container'],'started_at':stamp,'sha256':hashlib.sha256(candidate).hexdigest()};changed=False
  try:
   info=json.loads(docker('inspect',s['container']).stdout)[0]
   mounts={m['Destination']:m['Source'] for m in info['Mounts']}
   if mounts.get(s['dest'])!=str(s['running']) or info['Config']['Image']!=s['image']:raise RuntimeError('Unexpected deployment target')
   r['candidate_checks']=qualify(s,work/'validation',candidate.decode())
   changed=True;install(s,candidate);r['live_checks']=verify(s)
   cmd=['/venv/bin/python','-c',f'import hashlib;print(hashlib.sha256(open({s["dest"]!r},"rb").read()).hexdigest())'] if name=='recommendation' else ['php','-r',f"echo hash_file('sha256', '{s['dest']}');"]
   actual=docker('exec',s['container'],*cmd).stdout.strip()
   if actual!=r['sha256']:raise RuntimeError('Deployed source hash mismatch')
   r['status']='deployed_verified'
  except Exception as exc:
   r.update(status='rejected_before_deploy',error=str(exc))
   if changed:
    try:install(s,old);r['status']='rolled_back';r['rollback_checks']=verify(s)
    except Exception as err:r['rollback_error']=str(err)
   raise
  finally:
   r['finished_at']=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
   (work/'result.json').write_text(json.dumps(r,indent=2));print(json.dumps({'evidence':str(work),**r}),flush=True)
