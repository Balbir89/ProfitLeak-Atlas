"""Expert upgrade regression tests; no external packages required."""
import csv,json,math,sqlite3,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from risk_layer import robust_stats,robust_z,score_payment,drift_psi
from case_workflow import connect,init,assign,add_evidence,transition,record_cash,export

class TestRiskMath(unittest.TestCase):
 def test_robust_center(self):
  median,scale,_=robust_stats([100]*20)
  self.assertAlmostEqual(robust_z(100,median,scale),0,places=7)
 def test_robust_spike(self):
  med,scale,_=robust_stats([100]*30)
  self.assertGreater(robust_z(5000,med,scale),4.5)
 def test_no_negative_loss_from_statistical_model(self):
  self.assertGreater(score_payment('Duplicate payment',.9,0,.1),score_payment('No exception',0,0,.1))
 def test_score_is_bounded(self):
  for z in [-20,0,20,200]: self.assertTrue(0<=score_payment('No exception',0,z,.7)<=100)
 def test_psi_identity(self):self.assertAlmostEqual(drift_psi(list(range(100)),list(range(100))),0,places=9)
 def test_psi_shift(self):self.assertGreater(drift_psi(list(range(100)),list(range(500,600))),0.2)

class TestWorkflow(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'workflow.db'
  init(self.db)
  with connect(self.db) as c:
   financial=c.execute('SELECT payment_id FROM audit_case WHERE financial_exposure_eur>0 LIMIT 1').fetchone()
   nonfinancial=c.execute('SELECT payment_id FROM audit_case WHERE financial_exposure_eur=0 LIMIT 1').fetchone()
   self.fin=financial['payment_id'];self.ctrl=nonfinancial['payment_id']
 def tearDown(self):self.temp.cleanup()
 def test_idempotent_init(self):
  self.assertEqual(init(self.db),200)
 def test_ownership_and_event_trail(self):
  assign(self.fin,'Case Analyst','Supervisor',db=self.db)
  with connect(self.db) as c:
   row=c.execute('SELECT owner FROM audit_case WHERE payment_id=?',(self.fin,)).fetchone()
   self.assertEqual(row['owner'],'Case Analyst')
   self.assertEqual(c.execute("SELECT count(*) FROM audit_event WHERE payment_id=? AND action='ASSIGN'",(self.fin,)).fetchone()[0],1)
 def test_no_verify_without_evidence(self):
  transition(self.fin,'In Review','Analyst','Triage',self.db)
  with self.assertRaisesRegex(ValueError,'evidence'):transition(self.fin,'Verified','Analyst','Approved',self.db)
 def test_valid_evidence_verified_flow(self):
  transition(self.fin,'In Review','Analyst','Triage',self.db)
  add_evidence(self.fin,'DEMO://bank/123','Synthetic bank settlement evidence','Analyst',self.db)
  transition(self.fin,'Verified','Manager','Simulated review verified','dummy') if False else None
  transition(self.fin,'Verified','Manager','Simulated evidence reviewed',self.db)
  with connect(self.db) as c:self.assertEqual(c.execute('SELECT status FROM audit_case WHERE payment_id=?',(self.fin,)).fetchone()[0],'Verified')
 def test_no_credit_without_verification(self):
  with self.assertRaisesRegex(ValueError,'Verify'):record_cash(self.fin,2,'Analyst','DEMO://credit/123',self.db)
 def test_no_cash_credit_for_control_only(self):
  transition(self.ctrl,'In Review','Analyst','Triage',self.db)
  add_evidence(self.ctrl,'DEMO://policy','Approval review','Analyst',self.db)
  transition(self.ctrl,'Verified','Manager','Approval breach confirmed',self.db)
  with self.assertRaisesRegex(ValueError,'control-only'):record_cash(self.ctrl,1,'Analyst','DEMO://credit/123',self.db)
 def test_no_overcredit(self):
  transition(self.fin,'In Review','Analyst','Triage',self.db)
  add_evidence(self.fin,'DEMO://bank','Synthetic example','Analyst',self.db)
  transition(self.fin,'Verified','Manager','Synthetic example verified',self.db)
  with connect(self.db) as c:e=c.execute('SELECT financial_exposure_eur FROM audit_case WHERE payment_id=?',(self.fin,)).fetchone()[0]
  with self.assertRaisesRegex(ValueError,'exceed'):record_cash(self.fin,e+100,'Analyst','DEMO://credit',self.db)
 def test_closed_is_terminal(self):
  transition(self.fin,'Rejected','Analyst','Valid contract adjustment',self.db)
  transition(self.fin,'Closed','Manager','No recovery due',self.db)
  with self.assertRaises(ValueError):transition(self.fin,'In Review','Analyst','Reopen requested',self.db)
 def test_workflow_export(self):
  folder=Path(self.temp.name)/'export'
  result=export(self.db,folder)
  self.assertEqual(result['actual_cash_recovered_in_synthetic_demonstration_eur'],0)
  self.assertTrue((folder/'audit_events.csv').exists())
 def test_invalid_actor_rejected(self):
  with self.assertRaisesRegex(ValueError,'required'):add_evidence(self.fin,'DEMO://receipt','Demo','',self.db)

class TestIntegratedEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.conn=sqlite3.connect(ROOT/'database/atlas.db');cls.conn.row_factory=sqlite3.Row
  cls.metrics=json.loads((ROOT/'data/marts/metrics.json').read_text())
  cls.risk=json.loads((ROOT/'data/marts/risk_model_validation.json').read_text())
  cls.challenge=json.loads((ROOT/'data/marts/challenge_validation.json').read_text())
 @classmethod
 def tearDownClass(cls):cls.conn.close()
 def test_full_scored_grain(self):
  self.assertEqual(self.conn.execute('SELECT count(*) FROM risk_scores').fetchone()[0],self.metrics['payments'])
 def test_unchanged_exposure(self):
  cases=self.conn.execute('SELECT ROUND(SUM(financial_exposure_eur),2) FROM risk_scores').fetchone()[0]
  self.assertAlmostEqual(cases,self.metrics['gross_estimated_loss_eur'],places=2)
 def test_control_risk_zero_loss(self):
  count=self.conn.execute("SELECT count(*) FROM risk_scores WHERE issue_type='Approval fragmentation' AND financial_exposure_eur<>0").fetchone()[0]
  self.assertEqual(count,0)
 def test_no_synthetic_truth_leakage(self):
  code=(ROOT/'src/risk_layer.py').read_text().split('if __name__')[0]
  self.assertNotIn('injected_truth',code)
  self.assertNotIn('injected_labels',code)
 def test_holdout_not_perfect(self):
  self.assertLess(self.challenge['precision'],1.)
  self.assertLess(self.challenge['recall'],1.)
  self.assertGreater(self.challenge['false_positive'],0)
  self.assertGreater(self.challenge['false_negative'],0)
 def test_holdout_confusion_sums(self):
  self.assertEqual(sum(self.challenge[k] for k in ('true_positive','false_positive','true_negative','false_negative')),1500)
 def test_cash_not_claimed(self):
  w=json.loads((ROOT/'data/marts/workflow_status.json').read_text())
  self.assertEqual(w['actual_cash_recovered_in_synthetic_demonstration_eur'],0)
 def test_training_before_holdout(self):self.assertTrue('2025-12' in self.risk['historical_training_window'])
 def test_github_files_below_100mb_except_rebuildable_db(self):
  offenders=[p.name for p in ROOT.rglob('*') if p.is_file() and p.stat().st_size>100*1024*1024 and p.name!='atlas.db']
  self.assertFalse(offenders,offenders)
 def test_pbip_structural(self):
  base=ROOT/'powerbi/ProfitLeak_Atlas_PBIP'
  pbip=json.loads((base/'ProfitLeak_Atlas.pbip').read_text())
  self.assertTrue(pbip['artifacts'][0]['report']['path'].endswith('.Report'))
  ref=json.loads((base/'ProfitLeak_Atlas.Report/definition.pbir').read_text())
  self.assertTrue((base/'ProfitLeak_Atlas.Report'/ref['datasetReference']['byPath']['path']).is_dir())
  visuals=list((base/'ProfitLeak_Atlas.Report/definition/pages').rglob('visual.json'))
  self.assertGreaterEqual(len(visuals),8)
  for visual in visuals:
   v=json.loads(visual.read_text());self.assertTrue(v['visual']['query']['queryState'])
   self.assertEqual(len(v['name']),20)
 def test_workbook_has_new_sheets(self):
  x=ROOT/'excel/ProfitLeak_Atlas_Expert.xlsx';self.assertTrue(x.exists())
  with zipfile.ZipFile(x) as f:
   xml=f.read('xl/workbook.xml').decode('utf8')
  self.assertIn('Risk Validation',xml);self.assertIn('Audit Workflow',xml)

if __name__=='__main__':unittest.main()
