"""Fixed lab deployment entrypoint; source tests plus independent live acceptance checks."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import sys
sys.path.insert(0,str(config.REPO/'modules/fault-injector'))
from lab_runtime import deploy, LABS
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in LABS:raise SystemExit('Expected recommendation or quote')
 deploy(sys.argv[1])
