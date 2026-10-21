import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import selfheal_api

ROOT=Path(__file__).resolve().parents[1]
class ConfigTests(unittest.TestCase):
    def test_relative_paths_resolve_against_config_not_working_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            config=Path(temp)/'settings.json';config.write_text(json.dumps({'checkout_dir':'repair','projects_dir':'projects'}))
            env={k:v for k,v in os.environ.items() if not k.startswith('SELF_HEAL_')};env['SELF_HEAL_CONFIG']=str(config)
            code='import selfheal_config as c;print(c.CHECKOUT);print(c.PROJECTS)'
            out=subprocess.check_output([sys.executable,'-c',code],env=env,cwd=ROOT,text=True).splitlines()
            self.assertEqual(out,[str(Path(temp)/'repair'),str(Path(temp)/'projects')])
    def test_environment_override_and_missing_rule_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            env=dict(os.environ,SELF_HEAL_CONFIG=str(Path(temp)/'none.json'),SELF_HEAL_CHECKOUT_DIR=str(Path(temp)/'override'))
            out=subprocess.check_output([sys.executable,'-c','import selfheal_config as c;print(c.CHECKOUT)'],env=env,cwd=ROOT,text=True).strip()
            self.assertEqual(out,str(Path(temp)/'override'))
            r=subprocess.run([sys.executable,'-c',"import selfheal_config as c;c.require_rule('quote')"],env=env,cwd=ROOT,capture_output=True)
            self.assertNotEqual(r.returncode,0)
    def test_http_errors_do_not_expose_server_payload_or_credential(self):
        from urllib.error import HTTPError
        from io import BytesIO
        error=HTTPError('http://localhost',403,'Denied',{},BytesIO(b'private query contents'))
        with patch.object(selfheal_api,'credential',return_value='dummy-unit-value'),patch.object(selfheal_api.urllib.request,'urlopen',side_effect=error):
            with self.assertRaisesRegex(RuntimeError,'HTTP 403') as e:selfheal_api.api('/api/v1/rules')
            self.assertNotIn('private',str(e.exception));self.assertNotIn('dummy',str(e.exception))
