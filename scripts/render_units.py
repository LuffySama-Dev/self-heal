"""Render user-service templates into ignored local output; never install/start them."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import selfheal_config as config

def escape(value):
    value=str(value)
    if '\n' in value or '\r' in value:raise ValueError('Newlines are not allowed in service paths')
    return value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')

if __name__=='__main__':
    out=config.REPO/'.local/units';out.mkdir(parents=True,exist_ok=True)
    for template in config.REPO.glob('modules/*/*.service.in'):
        text=template.read_text().replace('@REPO@',escape(config.REPO)).replace('@CONFIG@',escape(config.CONFIG_PATH))
        (out/template.name.removesuffix('.in')).write_text(text)
    operator=dict(config.VALUES)
    operator.update({
      'projects_dir':str(config.PROJECTS), 'checkout_dir':str(config.CHECKOUT),
      'payment_dir':str(config.PAYMENT_DIR), 'labs_dir':str(config.LABS_DIR),
      'hermes_home':str(config.HERMES_HOME), 'incident_state_dir':str(config.INCIDENT_STATE),
      'rules_file':'/opt/self-heal-injector/.local/rules.json',
      'docker_host':config.DOCKER_HOST, 'docker_network':config.NETWORK,
      'image_prefix':config.IMAGE_PREFIX
    })
    (config.REPO/'.local/operator-config.json').write_text(json.dumps(operator,indent=2))
    (config.REPO/'.local/operator-config.json').chmod(0o600)
    print('Rendered units under .local/units; inspect them before installing.')
