"""Exercise every current operator in disposable containers, without injecting live faults."""
import json
import os
from pathlib import Path
import injector

os.umask(0o077)
root=Path.home()/'.local/state/self-heal-injector/qualification'
root.mkdir(parents=True,exist_ok=True)
source=injector.SOURCE.read_text()
results=[]
for name,candidate in [('healthy-baseline',source),*injector.candidates(source)]:
    r=injector.validate_source(root/name,candidate,name!='healthy-baseline')
    results.append({'operator':name,'result':r})
    print(name,'calls:',r['calls'],'failures:',r['failures'],flush=True)
(root/'results.json').write_text(json.dumps(results,indent=2))
