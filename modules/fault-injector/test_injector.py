import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import injector

class InjectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        (root/'requests.js').write_text('// unit-test probe fixture')
        mocked=patch.object(injector,'DRILL',root)
        mocked.start();self.addCleanup(mocked.stop)

    def test_seed_replays_exact_change(self):
        source='\n'.join(old for _,old,_ in injector.OPERATORS)
        # The expiry anchor appears in two operators; use one occurrence in the fixture.
        source='\n'.join(dict.fromkeys(source.splitlines()))
        self.assertEqual(injector.sample(source,1337),injector.sample(source,1337))
        self.assertEqual(len(injector.candidates(source)),4)
    def test_unknown_source_fails_closed(self):
        with self.assertRaises(RuntimeError):injector.sample('something else',1)
    def test_ambiguous_anchor_is_excluded(self):
        old=injector.OPERATORS[1][1]
        self.assertEqual(injector.candidates(old+'\n'+old),[])
    def test_one_source_change_and_no_feature_flag_changes(self):
        source="""if ((currentYear * 12 + currentMonth) > (year * 12 + month)) {}
if (!valid) {}
if (!['visa', 'mastercard'].includes(cardType)) {}
flags.getNumberValue('paymentFailure', 0);
flags.getBooleanValue('emitRawPii', false);
"""
        for name,candidate in injector.candidates(source):
            self.assertEqual(sum(a!=b for a,b in zip(source.splitlines(),candidate.splitlines())),1,name)
            self.assertEqual([l for l in source.splitlines() if 'getNumberValue' in l or 'getBooleanValue' in l], [l for l in candidate.splitlines() if 'getNumberValue' in l or 'getBooleanValue' in l])
    def test_compile_failure_never_launches_candidate(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(injector,'docker',side_effect=RuntimeError('syntax')) as call:
            with self.assertRaises(RuntimeError):injector.validate_source(Path(tmp),'invalid(',True)
            self.assertEqual(call.call_count,1)
            self.assertIn('--check',call.call_args.args)
    def test_no_observable_fault_rejected_and_container_removed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(injector,'docker') as call, patch.object(injector.time,'sleep'), patch.object(injector,'probe',return_value=[{'ok':True}]*6):
            with self.assertRaises(RuntimeError):injector.validate_source(Path(tmp),'valid',True)
            self.assertEqual(call.call_args.args[:2],('rm','-f'))
    def test_startup_transport_failure_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(injector,'docker') as call, patch.object(injector.time,'sleep'), patch.object(injector,'probe',return_value=[{'ok':False,'message':'No connection established'}]*6):
            with self.assertRaises(RuntimeError):injector.validate_source(Path(tmp),'valid',True)
            self.assertEqual(call.call_args.args[:2],('rm','-f'))

class RecoveryGuardTests(unittest.TestCase):
    def test_failed_live_install_restores_baseline(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source.js'; running=root/'running.js'
            healthy='if (!valid) {}';source.write_text(healthy);running.write_text(healthy)
            args=SimpleNamespace(seed=1,command='run',timeout_minutes=5)
            with patch.object(injector,'SOURCE',source), patch.object(injector,'RUNNING',running), patch.object(injector,'DRILL',root), patch.object(injector,'check_target'), patch.object(injector,'validate_source',return_value={}), patch.object(injector,'install_source',side_effect=RuntimeError('startup failed')), patch.object(injector,'restore') as restore:
                with self.assertRaises(RuntimeError):injector.run(args,root)
                restore.assert_called_once_with(healthy.encode())
                report=json.loads(next(root.glob('*/result.json')).read_text())
                self.assertEqual(report['cleanup'],'healthy_baseline_restored_not_agent_repair')
                self.assertEqual(report['status'],'failed')
    def test_second_run_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'lock'
            with injector.locked(p):
                with self.assertRaises(BlockingIOError):
                    with injector.locked(p):pass

if __name__=='__main__':unittest.main()
