import json
import unittest
from unittest.mock import patch
import bridge

class EvidenceTests(unittest.TestCase):
    def row(self, role, content, tool=None):
        return (1, 'session', role, content, tool, 1000.25)
    def test_scope(self):
        self.assertIsNone(bridge.notification('Notification payload: '+json.dumps({'alerts':[{'labels':{'ruleId':'unrelated'}}]})))
    def test_reasoning_excluded(self):
        self.assertIsNone(bridge.evidence(self.row('assistant','private thoughts'), 'incident'))
    def test_failed_patch_not_fix(self):
        self.assertIsNone(bridge.evidence(self.row('tool','{"success":false}', 'patch'), 'incident'))
    def test_test_counts_no_raw_output(self):
        e=bridge.evidence(self.row('tool',json.dumps({'output':'secret=not-exported\nℹ pass 7\nℹ fail 4','exit_code':1}),'terminal'),'incident')
        self.assertIn('fail 4',e['body']);self.assertNotIn('secret',e['body']);self.assertEqual(e['timestamp'],1000.25)
    def test_attempt_not_deployment(self):
        e=bridge.evidence(self.row('tool',json.dumps({'output':'deploy_lab.py started'}),'terminal'),'incident')
        self.assertIsNone(e)
    def test_partial_rejection_raises(self):
        with patch('bridge.urllib.request.urlopen') as url:
            url.return_value.__enter__.return_value.read.return_value=b'{"partialSuccess":{"rejectedLogRecords":"1"}}'
            with self.assertRaises(RuntimeError):bridge.export([bridge.event('a',100,'test','body')],'http://localhost',200)
    def test_candidate_probe_summary_excludes_raw_rows(self):
        result={'output':json.dumps({'calls':3,'failures':0,'rows':[{'secret':'not-exported'}]}),'exit_code':0}
        e=bridge.evidence(self.row('tool',json.dumps(result),'terminal'),'incident')
        self.assertEqual(e['stage'],'tests');self.assertIn('3 calls',e['body']);self.assertNotIn('secret',e['body'])
    def test_event_id_stable(self):
        self.assertEqual(bridge.event('a',100,'stage','body')['id'],bridge.event('a',100,'stage','body')['id'])

if __name__=='__main__':unittest.main()

class MilestoneTests(unittest.TestCase):
    def test_milestones_match_successful_patch_and_verified_artifact(self):
        import tempfile
        import sqlite3
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); db=root/'hermes.db'
            with sqlite3.connect(db) as c:
                c.execute('create table sessions (id text,started_at real,ended_at real,end_reason text,source text)')
                c.execute('create table messages (id integer,session_id text,role text,content text,tool_name text,timestamp real,tool_calls text,tool_call_id text)')
                c.execute("insert into sessions values ('s',100,200,'webhook_complete','webhook')")
                alert={'labels':{'ruleId':bridge.RULE},'status':'firing','startsAt':'1970-01-01T00:01:30Z','endsAt':'0001-01-01T00:00:00Z'}
                artifact=root/'payment-repair-drill/deployments/one/result.json'
                artifact.parent.mkdir(parents=True)
                artifact.write_text(json.dumps({'container':'payment-repair-lab','started_at':'19700101T000230Z','finished_at':'1970-01-01T00:02:40Z','status':'deployed_verified'}))
                rows=[(1,'s','user','Notification payload: '+json.dumps({'alerts':[alert]}),None,100,None,None),
                      (2,'s','assistant','',None,110,json.dumps([{'id':'patch1','function':{'name':'patch'}}]),None),
                      (3,'s','tool',json.dumps({'success':True,'diff':'--- a/src/payment/charge.js\n+++ b/src/payment/charge.js\n'}),'patch',111,None,'patch1'),
                      (4,'s','tool',json.dumps({'output':str(artifact.parent)}),'terminal',161,None,'deploy')]
                c.executemany('insert into messages values (?,?,?,?,?,?,?,?)',rows)
            with patch.object(bridge.config,'PAYMENT_DIR',root/'payment-repair-drill'), patch.object(bridge.config,'LABS_DIR',root/'self-heal-labs'):
                events=bridge.collect(db)
                stages={e['stage']:e['timestamp'] for e in events}
                self.assertEqual(stages['alert_fired'],90)
                self.assertEqual(stages['repair_started'],110)
                self.assertEqual(stages['deployment_started'],150)
                self.assertEqual(stages['deployment_verified'],160)
                self.assertNotIn('alert_resolved',stages)
                artifact.write_text(json.dumps({'container':'payment-repair-lab','started_at':'19700101T000230Z','finished_at':'1970-01-01T00:02:40Z','status':'rolled_back'}))
                stages={e['stage'] for e in bridge.collect(db)}
                self.assertNotIn('deployment_verified',stages)
                self.assertNotIn('deployment_started',stages)
