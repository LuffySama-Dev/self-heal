"""Prepare new isolated labs. Never overwrite existing containers or source files."""
import argparse,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import selfheal_config as config
sys.path.insert(0,str(config.REPO/'modules/fault-injector'))
import lab_runtime as lab

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    names=['flagd-repair-lab','payment-repair-lab','recommendation-repair-lab','quote-repair-lab']
    required=[config.CHECKOUT/'src/payment/charge.js',*[s['source'] for s in lab.LABS.values()]]
    if not all(f.is_file() for f in required):raise SystemExit('Prepare the pinned repair checkout first; see SETUP.md')
    for name in names:
        if lab.docker('inspect',name,check=False).returncode==0:raise SystemExit('Existing container; refusing to replace: '+name)
    lab.docker('network','inspect',config.NETWORK)
    if not args.apply:
        print('Preflight passed. --apply creates four isolated lab containers; no host ports are published.');return
    # Preflight all destinations before copying; preserve edits and prior snapshots.
    outputs=[config.PAYMENT_DIR/'running-charge.js',config.PAYMENT_DIR/'requests.js',config.PAYMENT_DIR/'flags.json',config.CHECKOUT/'src/payment/charge.test.js',*[s['running'] for s in lab.LABS.values()]]
    if any(f.exists() for f in outputs):raise SystemExit('Lab files already exist; refusing to overwrite')
    config.PAYMENT_DIR.mkdir(parents=True,exist_ok=True)
    shutil.copy2(required[0],outputs[0]);shutil.copy2(config.REPO/'fixtures/payment/requests.js',outputs[1]);shutil.copy2(config.REPO/'fixtures/payment/charge.test.js',outputs[3])
    outputs[2].write_text(json.dumps({'flags':{k:{'state':'ENABLED','variants':{'off':v},'defaultVariant':'off'} for k,v in [('paymentFailure',0),('emitRawPii',False)]}}))
    (config.PAYMENT_DIR/'deploy.lock').touch();(config.PAYMENT_DIR/'injector.lock').touch()
    created=[]
    try:
        lab.docker('run','-d','--name',names[0],'--network',config.NETWORK,'--mount',f'type=bind,src={outputs[2]},dst=/etc/flags.json,readonly',config.setting('flagd_image','ghcr.io/open-feature/flagd:v0.16.0'),'start','--uri','file:/etc/flags.json');created.append(names[0])
        env={'FLAGD_HOST':names[0],'FLAGD_PORT':'8013','PAYMENT_PORT':'50051','OTEL_SERVICE_NAME':names[1],'OTEL_RESOURCE_ATTRIBUTES':'service.namespace=self-heal-repair-lab','OTEL_EXPORTER_OTLP_ENDPOINT':config.setting('collector_grpc_url','http://otel-collector:4317'),'OTEL_EXPORTER_OTLP_PROTOCOL':'grpc','OTEL_METRIC_EXPORT_INTERVAL':'10000'}
        cmd=['run','-d','--name',names[1],'--network',config.NETWORK,'--mount',f'type=bind,src={outputs[0]},dst=/usr/src/app/charge.js,readonly','--mount',f'type=bind,src={config.PAYMENT_DIR},dst=/drill,readonly']
        for k,v in env.items():cmd+=['-e',k+'='+v]
        lab.docker(*cmd,config.IMAGE_PREFIX+'payment');created.append(names[1])
        for s in lab.LABS.values():
            s['directory'].mkdir(parents=True,exist_ok=True);shutil.copy2(s['source'],s['running']);(s['directory']/'deploy.lock').touch()
            lab.start_container(s,s['container'],s['running']);created.append(s['container'])
    except Exception:
        print('Setup incomplete; created containers: '+', '.join(created)+'. Inspect before retrying. Files retained.',file=sys.stderr);raise
    print('Created isolated labs. Verify each service before enabling alerts; see SETUP.md.')
if __name__=='__main__':main()
