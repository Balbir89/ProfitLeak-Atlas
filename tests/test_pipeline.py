"""Run: python -m unittest discover -s tests -v (from project root)"""
import json,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestCaseStudy(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.db=sqlite3.connect(ROOT/'database/atlas.db');cls.metrics=json.loads((ROOT/'data/marts/metrics.json').read_text())
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def count(self,q):return self.db.execute(q).fetchone()[0]
 def test_payment_grain(self):self.assertEqual(self.count('SELECT COUNT(*) FROM fact_payment'),self.metrics['payments'])
 def test_all_payments_mapped_once(self):self.assertEqual(self.count('SELECT COUNT(*) FROM case_mart'),self.metrics['payments'])
 def test_no_negative_loss(self):self.assertEqual(self.count('SELECT COUNT(*) FROM case_mart WHERE estimated_gross_loss_eur<0'),0)
 def test_nonfinancial_risk_is_zero_eur(self):self.assertEqual(self.count("SELECT COUNT(*) FROM case_mart WHERE issue_type='Approval fragmentation' AND estimated_gross_loss_eur<>0"),0)
 def test_recovery_not_exceed_gross(self):self.assertLessEqual(self.metrics['modeled_recoverable_eur'],self.metrics['gross_estimated_loss_eur'])
 def test_issues_injected_visible(self):self.assertEqual(self.count("SELECT COUNT(*) FROM case_mart WHERE issue_type<>'No exception'"),self.metrics['flagged_payments'])
 def test_synthetic_truth_isolated(self):
  self.assertNotIn('injected_truth',(ROOT/'sql/02_detection.sql').read_text())
 def test_no_orphans(self):self.assertEqual(self.count('SELECT COUNT(*) FROM fact_payment p LEFT JOIN dim_contract c USING(vendor_id) WHERE c.vendor_id IS NULL'),0)
if __name__=='__main__':unittest.main()
