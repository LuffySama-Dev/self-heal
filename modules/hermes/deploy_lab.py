"""Pre-authorized payment lab rollout with tests, live checks and rollback."""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
import selfheal_config as config
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

CHECKOUT = config.CHECKOUT
DRILL = config.PAYMENT_DIR
IMAGE = config.IMAGE_PREFIX+'payment'
CONTAINER = 'payment-repair-lab'


def docker(*args, timeout=120):
    env = os.environ.copy()
    for key in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
        env.pop(key, None)
    result = subprocess.run(['docker', '--host', config.DOCKER_HOST, *args],
                            text=True, capture_output=True, timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def verify():
    last = None
    for _ in range(10):
        try:
            output = docker('exec', CONTAINER, '/nodejs/bin/node', '/drill/requests.js', '6', timeout=75)
            rows = [json.loads(line) for line in output.splitlines() if line.startswith('{')]
            if rows[-1] != {'success': 6, 'failures': 0}:
                raise RuntimeError('Live current-month/future-year checks failed: ' + output)
            return rows
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            last = error
            time.sleep(2)
    raise RuntimeError(str(last))


def main():
    with (DRILL / 'deploy.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        evidence = DRILL / 'deployments' / stamp
        evidence.mkdir(parents=True, exist_ok=False)
        report = {'container': CONTAINER, 'started_at': stamp}
        running = DRILL / 'running-charge.js'
        old = running.read_bytes()
        candidate = (CHECKOUT / 'src/payment/charge.js').read_bytes()
        (evidence / 'previous-charge.js').write_bytes(old)
        (evidence / 'candidate-charge.js').write_bytes(candidate)
        report['sha256'] = hashlib.sha256(candidate).hexdigest()
        deployed = False
        try:
            info = json.loads(docker('inspect', CONTAINER))[0]
            mounts = {m['Destination']: m for m in info['Mounts']}
            if mounts['/usr/src/app/charge.js']['Source'] != str(running):
                raise RuntimeError('Unexpected lab source mount')
            if info['Config']['Image'] != IMAGE:
                raise RuntimeError('Unexpected lab image')
            with tempfile.TemporaryDirectory(prefix='payment-lab-tests-') as temp:
                stage = Path(temp)
                stage.chmod(0o755)
                (stage / 'charge.js').write_bytes(candidate)
                (stage / 'charge.test.js').write_bytes((CHECKOUT / 'src/payment/charge.test.js').read_bytes())
                for zone in ('UTC', 'America/Los_Angeles'):
                    output = docker('run', '--rm', '--network', 'none', '-e', 'NODE_OPTIONS=',
                                    '-e', 'TZ=' + zone, '-v', f'{stage}:/lab:ro', '-w', '/lab',
                                    IMAGE, '--test', 'charge.test.js')
                    (evidence / ('tests-' + zone.replace('/', '-') + '.txt')).write_text(output)
            docker('stop', '-t', '3', CONTAINER)
            deployed = True
            running.write_bytes(candidate)
            docker('start', CONTAINER)
            report['live_checks'] = verify()
            actual = docker('exec', CONTAINER, '/nodejs/bin/node', '-e',
                            'console.log(require("crypto").createHash("sha256").update(require("fs").readFileSync("/usr/src/app/charge.js")).digest("hex"));process.exit(0)').strip()
            if actual != report['sha256']:
                raise RuntimeError('Deployed hash mismatch')
            report['status'] = 'deployed_verified'
        except Exception as error:
            report['error'] = str(error)
            report['status'] = 'rejected_before_deploy'
            if deployed:
                try:
                    docker('stop', '-t', '3', CONTAINER)
                    running.write_bytes(old)
                    docker('start', CONTAINER)
                    report['status'] = 'rolled_back'
                    try:
                        report['rollback_checks'] = verify()
                    except Exception as check_error:
                        report['rollback_health_error'] = str(check_error)
                except Exception as rollback_error:
                    report['status'] = 'rollback_failed'
                    report['rollback_error'] = str(rollback_error)
            raise
        finally:
            report['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            (evidence / 'result.json').write_text(json.dumps(report, indent=2))
            print(json.dumps({'evidence': str(evidence), **report}))


if __name__ == '__main__':
    main()
