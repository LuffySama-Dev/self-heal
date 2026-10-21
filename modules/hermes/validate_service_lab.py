"""Run syntax and independent request checks against a disposable candidate."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(config.REPO/'modules/fault-injector'))
from lab_runtime import LABS,qualify
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in LABS:raise SystemExit('Expected recommendation or quote')
 s=LABS[sys.argv[1]]
 with tempfile.TemporaryDirectory() as tmp:
  print(json.dumps(qualify(s,Path(tmp),s['source'].read_text())))
