"""Run isolated unit suites without local configuration, Docker or credentials."""
import os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='self-heal-unit-') as tmp:
    env={k:v for k,v in os.environ.items() if not k.startswith('SELF_HEAL_')}
    env['SELF_HEAL_CONFIG']=str(Path(tmp)/'missing.json')
    for folder in ['tests','modules/fault-injector','modules/hermes','modules/incident-live']:
        subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/folder),'-q'],env=env,cwd=ROOT,check=True)
