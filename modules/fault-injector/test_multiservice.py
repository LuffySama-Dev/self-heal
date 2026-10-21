import json,random,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import lab_runtime as lab
import injector

class MultiServiceTests(unittest.TestCase):
 def test_candidate_family_coverage(self):
  for name,s in lab.LABS.items():
   source={
    'recommendation': "num_return = min(max_responses, num_products)\nproduct_catalog_stub.ListProducts(demo_pb2.Empty())\nproduct_catalog_stub.ListProducts(demo_pb2.Empty())\n        prod_list = get_product_list(request.product_ids)",
    'quote': "$response->getBody()->write($payload);\n$data = calculateQuote($jsonObject);"
   }[name]
   for kind,old,new in injector.EXTRA_OPERATORS[name]:
    self.assertIn(old,source,kind)
    self.assertNotEqual(old,new)
 def test_auto_service_selection_reproducible_and_covers_all(self):
  services=['payment','recommendation','quote']
  a=[random.Random(str(i)+':service').choice(services) for i in range(100)]
  b=[random.Random(str(i)+':service').choice(services) for i in range(100)]
  self.assertEqual(a,b);self.assertEqual(set(a),set(services))
 def test_service_configuration_can_return_to_payment(self):
  try:
   injector.configure_service('quote')
   self.assertEqual(injector.TARGET,'quote-repair-lab')
   injector.configure_service('payment')
   self.assertEqual(injector.TARGET,'payment-repair-lab')
   self.assertEqual(len(injector.OPERATORS),4)
  finally:
   injector.configure_service('payment')
 def test_syntax_failure_cannot_start_candidate(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(lab,'syntax',side_effect=RuntimeError('invalid')),patch.object(lab,'start_container') as start:
   with self.assertRaises(RuntimeError):lab.qualify(lab.LABS['quote'],Path(temp),'invalid',True)
   start.assert_not_called()
 def test_failed_live_rollout_restores_previous_snapshot(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'candidate';running=root/'running';source.write_text('fixed');running.write_text('faulty')
   spec={**lab.LABS['quote'],'directory':root,'source':source,'running':running}
   info=[{'Config':{'Image':spec['image']},'Mounts':[{'Destination':spec['dest'],'Source':str(running)}]}]
   from types import SimpleNamespace
   with patch.dict(lab.LABS,{'quote':spec}),patch.object(lab,'docker',return_value=SimpleNamespace(stdout=json.dumps(info))),patch.object(lab,'qualify',return_value={}),patch.object(lab,'install') as install,patch.object(lab,'verify',side_effect=[RuntimeError('probe failed'),[]]):
    with self.assertRaises(RuntimeError):lab.deploy('quote')
    self.assertEqual([c.args[1] for c in install.call_args_list],[b'fixed',b'faulty'])
    r=json.loads(next((root/'deployments').glob('*/result.json')).read_text())
    self.assertEqual(r['status'],'rolled_back')

if __name__=='__main__':unittest.main()
