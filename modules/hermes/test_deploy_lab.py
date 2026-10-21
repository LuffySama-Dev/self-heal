import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import deploy_lab


class DeploymentTests(unittest.TestCase):
    def exercise(self, failure):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / 'checkout'
            source = checkout / 'src/payment'
            source.mkdir(parents=True)
            (source / 'charge.js').write_text('candidate')
            (source / 'charge.test.js').write_text('test')
            running = root / 'running-charge.js'
            running.write_text('previous')
            calls = []

            def docker(*args, **kwargs):
                calls.append(args)
                if args[0] == 'inspect':
                    return json.dumps([{'Config': {'Image': deploy_lab.IMAGE}, 'Mounts': [
                        {'Destination': '/usr/src/app/charge.js', 'Source': str(running)}]}])
                if args[0] == 'run' and failure == 'tests':
                    raise RuntimeError('regression failed')
                if args[0] == 'exec':
                    return 'wrong hash'
                return 'ok'

            with patch.object(deploy_lab, 'CHECKOUT', checkout), patch.object(deploy_lab, 'DRILL', root), \
                    patch.object(deploy_lab, 'docker', side_effect=docker), \
                    patch.object(deploy_lab, 'verify', side_effect=([RuntimeError('live failed'), []]
                                 if failure == 'live' else [[], []])), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    deploy_lab.main()
            report = json.loads(next((root / 'deployments').glob('*/result.json')).read_text())
            self.assertEqual(running.read_text(), 'previous')
            self.assertEqual(report['status'], 'rejected_before_deploy' if failure == 'tests' else 'rolled_back')
            if failure == 'tests':
                self.assertFalse(any(c[0] in ('stop', 'start') for c in calls))
            else:
                self.assertEqual(sum(c[0] == 'start' for c in calls), 2)

    def test_failed_tests_preserve_deployment(self):
        self.exercise('tests')

    def test_failed_live_checks_restore_previous_snapshot(self):
        self.exercise('live')

    def test_wrong_deployed_hash_rolls_back(self):
        self.exercise('hash')
