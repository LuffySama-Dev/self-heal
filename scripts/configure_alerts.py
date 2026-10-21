"""Preview or create disabled alert rules and save IDs outside the public file set."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import selfheal_config as config
from selfheal_api import api

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--group',choices=['symptom','availability'],required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    folder='fault-injector' if args.group=='symptom' else 'availability'
    templates=json.loads((config.REPO/'modules'/folder/'alert-rules.example.json').read_text())
    if not args.apply:
        for name,rule in templates.items():print(name+': '+rule['alert']+' (disabled)')
        return
    os.umask(0o077)
    data=json.loads(config.RULES_PATH.read_text()) if config.RULES_PATH.exists() else {}
    ids=data.setdefault(args.group,{})
    config.RULES_PATH.parent.mkdir(parents=True,exist_ok=True)
    for name,rule in templates.items():
        if ids.get(name) and not ids[name].startswith('REPLACE_'):continue
        rule['disabled']=True
        ids[name]=api('/api/v1/rules',rule)['data']['id']
        temporary=config.RULES_PATH.with_suffix('.tmp')
        temporary.write_text(json.dumps(data,indent=2));temporary.replace(config.RULES_PATH)
        print('Created disabled rule for '+name)

if __name__=='__main__':main()
