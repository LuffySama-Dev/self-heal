#!/usr/bin/python3
"""Random, build-checked lab service source faults. Never sends the mutation to Hermes."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import secrets
import signal
import sqlite3
import subprocess
import tempfile
import time

PROJECTS = config.PROJECTS
CHECKOUT = config.CHECKOUT
DRILL = config.PAYMENT_DIR
SOURCE = CHECKOUT / 'src/payment/charge.js'
RUNNING = DRILL / 'running-charge.js'
IMAGE = config.IMAGE_PREFIX + 'payment'
TARGET = 'payment-repair-lab'
RULE = config.rules('symptom').get('payment')
DB = config.HERMES_HOME / 'state.db'
# Exact anchors fail closed if the source no longer matches this adapter.
OPERATORS = [
    ('boundary-inclusive', 'if ((currentYear * 12 + currentMonth) > (year * 12 + month))', 'if ((currentYear * 12 + currentMonth) >= (year * 12 + month))'),
    ('validation-negation', 'if (!valid)', 'if (valid)'),
    ('card-eligibility-negation', "if (!['visa', 'mastercard'].includes(cardType))", "if (['visa', 'mastercard'].includes(cardType))"),
    ('expiry-direction', 'if ((currentYear * 12 + currentMonth) > (year * 12 + month))', 'if ((currentYear * 12 + currentMonth) < (year * 12 + month))'),
]

PAYMENT_SETTINGS = (SOURCE, RUNNING, DRILL, IMAGE, TARGET, RULE, OPERATORS)
SERVICE = 'payment'
EXTRA_OPERATORS = {
 'recommendation': [
  ('sample-overflow', 'num_return = min(max_responses, num_products)', 'num_return = max(max_responses, num_products)'),
  ('catalog-method-mismatch', 'product_catalog_stub.ListProducts(demo_pb2.Empty())', 'product_catalog_stub.GetProducts(demo_pb2.Empty())'),
  ('blocking-latency', '        prod_list = get_product_list(request.product_ids)', "        __import__('time').sleep(1.5)\n        prod_list = get_product_list(request.product_ids)"),
 ],
 'quote': [
  ('response-method-mismatch', '$response->getBody()->write($payload);', '$response->getBoddy()->write($payload);'),
  ('blocking-latency', '$data = calculateQuote($jsonObject);', 'usleep(1500000); $data = calculateQuote($jsonObject);'),
 ]
}

def configure_service(name):
    global SERVICE, SOURCE, RUNNING, DRILL, IMAGE, TARGET, RULE, OPERATORS
    SERVICE=name
    if name=='payment':
        SOURCE,RUNNING,DRILL,IMAGE,TARGET,RULE,OPERATORS=PAYMENT_SETTINGS
        return
    import lab_runtime
    s=lab_runtime.LABS[name]
    SOURCE,RUNNING,DRILL,IMAGE,TARGET=s['source'],s['running'],s['directory'],s['image'],s['container']
    RULE=config.rules('symptom').get(name)
    OPERATORS=EXTRA_OPERATORS[name]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def docker(*args, timeout=60, check=True):
    env = {k:v for k,v in os.environ.items() if k not in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
    p = subprocess.run(['docker','--host',config.DOCKER_HOST,*args], env=env, text=True, capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError('Docker operation failed: '+p.stderr[-1200:])
    return p

def candidates(source):
    result=[]
    for name,old,new in OPERATORS:
        if source.count(old)==1:
            result.append((name, source.replace(old,new,1)))
        elif name=='catalog-method-mismatch' and source.count(old)==2:
            result.append((name, source.replace(old,new)))
    return result

def sample(source, seed):
    options=candidates(source)
    if not options:
        raise RuntimeError('No compatible source sites; target was not changed')
    return random.Random(seed).choice(options)

def probe(container, script='/drill/requests.js'):
    if SERVICE!='payment':
        import lab_runtime
        return lab_runtime.probe(lab_runtime.LABS[SERVICE],container)
    p=docker('exec',container,'/nodejs/bin/node',script,'6',timeout=35,check=False)
    rows=[]
    for line in p.stdout.splitlines():
        try: rows.append(json.loads(line))
        except ValueError: pass
    calls=[r for r in rows if isinstance(r,dict) and 'ok' in r]
    return calls if p.returncode==0 and len(calls)==6 else []

def validate_source(stage, source, expected_failure):
    if SERVICE!='payment':
        import lab_runtime
        return lab_runtime.qualify(lab_runtime.LABS[SERVICE],stage,source,expected_failure)
    stage.mkdir(parents=True,exist_ok=True)
    (stage/'charge.js').write_text(source)
    (stage/'requests.js').write_bytes((DRILL/'requests.js').read_bytes())
    stage.chmod(0o755)
    for file in stage.iterdir(): file.chmod(0o644)
    # Node --check validates JavaScript syntax before any runtime deployment.
    docker('run','--rm','--network','none','-e','NODE_OPTIONS=',
           '-v',f'{stage}:/candidate:ro',IMAGE,'--check','/candidate/charge.js')
    name='fault-probe-'+secrets.token_hex(6)
    try:
        docker('run','-d','--name',name,'--network',config.NETWORK,
               '-e','OTEL_SDK_DISABLED=true','-e','OTEL_SERVICE_NAME=fault-probe',
               '-e','FLAGD_HOST=flagd-repair-lab','-e','FLAGD_PORT=8013','-e','PAYMENT_PORT=50051',
               '-v',f'{stage}/charge.js:/usr/src/app/charge.js:ro',
               '-v',f'{stage}/requests.js:/probe/requests.js:ro',IMAGE)
        rows=[]
        for _ in range(12):
            time.sleep(1)
            rows=probe(name,'/probe/requests.js')
            # Transport errors while booting aren't a qualified application defect.
            if rows and not any(any(t in r.get('message','').lower() for t in ['no connection','connect econn','deadline exceeded']) for r in rows):
                break
        if len(rows)!=6:
            raise RuntimeError('Candidate did not serve six probe requests')
        failed=sum(not r['ok'] for r in rows)
        if (not expected_failure and failed) or (expected_failure and failed<3):
            raise RuntimeError('Candidate did not meet the expected runtime behavior')
        if any(any(t in r.get('message','').lower() for t in ['no connection','connect econn','deadline exceeded']) for r in rows):
            raise RuntimeError('Candidate failed to start; rejected before live injection')
        return {'calls':6,'failures':failed,'rows':rows}
    finally:
        docker('rm','-f',name,check=False)

@contextlib.contextmanager
def locked(path):
    with path.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield

def check_target():
    if SERVICE!='payment':
        import lab_runtime
        return lab_runtime.preflight(lab_runtime.LABS[SERVICE])
    info=json.loads(docker('inspect',TARGET).stdout)[0]
    mounts={m['Destination']:m for m in info['Mounts']}
    if info['Config']['Image']!=IMAGE or mounts['/usr/src/app/charge.js']['Source']!=str(RUNNING):
        raise RuntimeError('Unexpected target or source mount')
    if not info['State']['Running']:
        raise RuntimeError('Lab is not running')
    flags=json.loads((DRILL/'flags.json').read_text())['flags']
    for key in ['paymentFailure','emitRawPii']:
        f=flags[key]
        if f['variants'][f['defaultVariant']]:
            raise RuntimeError('Lab feature flags must remain off')
    rows=probe(TARGET)
    if len(rows)!=6 or not all(r['ok'] for r in rows):
        raise RuntimeError('Lab must be healthy before injection')

def install_source(source):
    if SERVICE!='payment':
        import lab_runtime
        return lab_runtime.install(lab_runtime.LABS[SERVICE],source,checkout=True)
    docker('stop','-t','3',TARGET)
    # Write in place: the running container bind-mount refers to this inode.
    SOURCE.write_bytes(source)
    RUNNING.write_bytes(source)
    docker('start',TARGET)

def restore(source):
    with locked(DRILL/'deploy.lock'):
        install_source(source)
        for _ in range(12):
            time.sleep(1)
            rows=probe(TARGET)
            if len(rows)==(6 if SERVICE=='payment' else 3) and all(r['ok'] for r in rows):
                return
        raise RuntimeError('Reset did not restore healthy live traffic')

def sessions_since(start):
    found=[]
    with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as c:
        for sid,ended,reason in c.execute("select id,ended_at,end_reason from sessions where source='webhook' and started_at>=?",(start,)):
            for content, in c.execute("select content from messages where session_id=? and role='user'",(sid,)):
                marker='Notification payload:'
                if marker not in (content or ''): continue
                try: payload=json.JSONDecoder().raw_decode(content.split(marker,1)[1].lstrip())[0]
                except ValueError: continue
                for alert in payload.get('alerts',[]):
                    if alert.get('labels',{}).get('ruleId')!=RULE:continue
                    opened=dt.datetime.fromisoformat(alert['startsAt'].replace('Z','+00:00')).timestamp()
                    if opened<start:continue
                    found.append({'id':sid,'status':alert['status'],'startsAt':alert['startsAt'],'endsAt':alert.get('endsAt'),'ended':ended,'reason':reason})
    return found

def verified_deployment(start, sessions):
    firing_ids={s['id'] for s in sessions if s['status']=='firing'}
    if not firing_ids:return None
    with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as c:
        for path in sorted((DRILL/'deployments').glob('*/result.json'),reverse=True):
            try:
                result=json.loads(path.read_text())
                end=dt.datetime.fromisoformat(result['finished_at'].replace('Z','+00:00')).timestamp()
            except (ValueError,KeyError):continue
            if end<start or result.get('status')!='deployed_verified':continue
            for sid in firing_ids:
                rows=c.execute("select content from messages where session_id=? and tool_name='terminal'",(sid,))
                if any(str(path.parent) in (r[0] or '') for r in rows):
                    return {'path':str(path),'result':result,'session':sid}
    return None

def save(path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2))
    temp.replace(path)

def run(args, state):
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)
    work=state/stamp;work.mkdir(mode=0o700)
    report={'run':stamp,'target':TARGET,'seed':args.seed if args.seed is not None else secrets.randbits(64), 'started_at':now(),'status':'preparing','algorithm':'python-random-choice-v1','operator_version':2,'service':SERVICE}
    baseline=SOURCE.read_bytes()
    if baseline!=RUNNING.read_bytes():raise RuntimeError('Checkout and running snapshot differ; refusing to overwrite pending edits')
    name,mutated=sample(baseline.decode(),report['seed'])
    report.update(operator=name,base_sha256=sha(baseline),candidate_sha256=sha(mutated.encode()))
    (work/'healthy-charge.js').write_bytes(baseline)
    (work/'candidate-charge.js').write_text(mutated)
    save(work/'result.json',report)
    print('Run '+stamp+': target '+TARGET+'; qualifying candidate. Mutation details stay in operator records.',flush=True)
    try:
        check_target()
        report['baseline_probe']=validate_source(work/'baseline',baseline.decode(),False)
        report['candidate_probe']=validate_source(work/'candidate',mutated,True)
    except Exception as exc:
        report.update(status='rejected_before_injection',error=str(exc),finished_at=now())
        save(work/'result.json',report)
        raise
    save(work/'result.json',report)
    if args.command=='check':
        report['status']='qualified_without_injection';save(work/'result.json',report)
        print('Qualified: valid syntax, healthy baseline and runtime failures reproduced. Live lab unchanged.',flush=True)
        return
    injected=False
    try:
        with locked(DRILL/'deploy.lock'):
            if SOURCE.read_bytes()!=baseline or RUNNING.read_bytes()!=baseline:
                raise RuntimeError('Source changed during qualification; refusing injection')
            injected=True
            install_source(mutated.encode())
        start=time.time();report.update(status='injected',injected_at=now());save(work/'result.json',report)
        print('Fault deployed. Waiting for authentic SigNoz → Hermes repair and recovery.',flush=True)
        deadline=time.monotonic()+args.timeout_minutes*60
        last_print=0;observed_failure=False;post_calls=[]
        while time.monotonic()<deadline:
            rows=probe(TARGET)
            with (work/'traffic.jsonl').open('a') as f:
                for row in rows:f.write(json.dumps(row)+'\n')
            observed_failure |= any(not r['ok'] for r in rows)
            sessions=sessions_since(start)
            deployment=verified_deployment(start,sessions)
            if deployment:
                post_calls=[json.loads(l) for l in (work/'traffic.jsonl').read_text().splitlines() if l]
                post_calls=[r for r in post_calls if r['time']>=deployment['result']['finished_at']]
            recovered=any(s['status']=='resolved' and s['reason']=='webhook_complete' for s in sessions)
            repaired=any(s['status']=='firing' and s['reason']=='webhook_complete' for s in sessions)
            if observed_failure and deployment and recovered and repaired and len(post_calls)>=12 and all(r['ok'] for r in post_calls):
                report.update(status='recovered_by_hermes',sessions=sessions,deployment=deployment,finished_at=now(),post_deployment_calls=len(post_calls),post_deployment_errors=0)
                save(work/'result.json',report)
                print('PASS: Hermes fixed, tested, deployed and processed recovery; post-deployment traffic is healthy.',flush=True)
                return
            if time.monotonic()-last_print>40:
                print(json.dumps({'time':now(),'traffic_failures':sum(not r['ok'] for r in rows),'traffic_calls':len(rows),'hermes_sessions':len(sessions),'deployment_verified':bool(deployment),'recovery_followup_complete':recovered}),flush=True)
                last_print=time.monotonic()
            time.sleep(10)
        raise TimeoutError('No verified automatic recovery before timeout')
    except BaseException as exc:
        report.update(status='failed',error=str(exc),finished_at=now())
        if injected:
            try:
                restore(baseline);report['cleanup']='healthy_baseline_restored_not_agent_repair'
            except Exception as reset_error:
                report['cleanup']='reset_failed';report['reset_error']=str(reset_error)
        save(work/'result.json',report)
        raise

def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Interrupted; restoring baseline if injection began')
    signal.signal(signal.SIGTERM, interrupted)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','run'])
    parser.add_argument('--seed',type=int)
    parser.add_argument('--service',choices=['auto','payment','recommendation','quote'],default='auto')
    parser.add_argument('--timeout-minutes',type=int,default=25)
    parser.add_argument('--development',action='store_true',help='Unprivileged development checkout only, not root-only installation')
    args=parser.parse_args()
    if not 5<=args.timeout_minutes<=30:parser.error('timeout must be 5–30 minutes')
    if os.geteuid()!=0 and not args.development:parser.error('Installed command requires sudo; development mode must be explicit')
    if args.seed is None:args.seed=secrets.randbits(64)
    selected=random.Random(str(args.seed)+':service').choice(['payment','recommendation','quote']) if args.service=='auto' else args.service
    configure_service(selected)
    if args.command=='run':config.require_rule(selected)
    os.umask(0o077)
    state=Path('/var/lib/self-heal-injector') if os.geteuid()==0 else Path.home()/'.local/state/self-heal-injector'
    state.mkdir(mode=0o700,parents=True,exist_ok=True)
    with locked(config.PAYMENT_DIR/'injector.lock'):
        run(args,state)

if __name__=='__main__':main()
