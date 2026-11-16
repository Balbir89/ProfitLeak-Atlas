"""External real-data ingestion and Power BI offline source checks."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from public_data_validation import scan
from verify_powerbi_source import checks

class TestPublicData(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'data/public/chicago_vendor_payments_observed.json').read_text())
 def test_public_source_provenance(self):
  self.assertIn('data.cityofchicago.org',self.data['source_url'])
  self.assertEqual(len(self.data['records']),44)
 def test_curated_real_rows_parse(self):
  result,alerts=scan(self.data['records'])
  self.assertEqual(result['records_inspected'],44)
  self.assertEqual(result['invalid_or_missing_rows'],0)
 def test_year_only_rollups_not_itemized(self):
  result,_=scan(self.data['records'])
  self.assertEqual(result['year_only_aggregate_rows'],5)
  self.assertEqual(result['itemized_date_rows'],39)
 def test_no_fraud_amount_inferred(self):
  summary,_=scan(self.data['records'])
  self.assertIsNone(summary['recoverable_loss_usd'])
  self.assertIsNone(summary['confirmed_fraud_cases'])
 def test_duplicate_record_is_only_a_review_candidate(self):
  r={'vendor_name':'Example vendor','voucher_number':'A-001','amount':'500','check_date':'01/01/2026','contract_number':'1'}
  result,alerts=scan([r,copy.deepcopy(r)])
  self.assertEqual(result['strict_duplicate_row_candidates'],1)
  self.assertEqual(len(alerts),1)
  self.assertFalse(alerts[0]['fraud_confirmed'])
 def test_distinct_voucher_same_amount_not_automatically_duplicate(self):
  r={'vendor_name':'Example vendor','voucher_number':'A-001','amount':'500','check_date':'01/01/2026','contract_number':'1'}
  r2={**r,'voucher_number':'A-002'}
  result,alerts=scan([r,r2])
  self.assertEqual(result['strict_duplicate_row_candidates'],0)
  self.assertFalse(alerts)
 def test_year_only_not_used_in_duplicate_signatures(self):
  r={'vendor_name':'Sample','amount':'200','check_date':'2022','contract_number':'22'}
  result,_=scan([r,r])
  self.assertEqual(result['strict_duplicate_row_candidates'],0)
  self.assertEqual(result['year_only_aggregate_rows'],2)
 def test_invalid_date_rejected(self):
  result,_=scan([{'vendor_name':'Sample','amount':'200','check_date':'02/31/2026','voucher_number':'V-1'}])
  self.assertEqual(result['invalid_or_missing_rows'],1)
 def test_nan_amount_rejected(self):
  result,_=scan([{'vendor_name':'Sample','amount':'NaN','check_date':'01/01/2026'}])
  self.assertEqual(result['invalid_or_missing_rows'],1)
 def test_reused_voucher_distinct_vendor_review_only(self):
  first={'vendor_name':'A','amount':'100','check_date':'01/01/2026','voucher_number':'V1'}
  second={**first,'vendor_name':'B'}
  result,_=scan([first,second])
  self.assertEqual(result['reused_voucher_across_distinct_details_candidates'],1)
  self.assertIsNone(result['confirmed_fraud_cases'])

class TestPowerBISource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.result=checks()
 def test_structural_passes(self):self.assertTrue(self.result['offline_source_checks_passed'])
 def test_all_bindings_resolved(self):self.assertEqual(self.result['checks_failed'],[])
 def test_three_pages(self):self.assertEqual(self.result['pages'],3)
 def test_no_native_desktop_claim(self):self.assertFalse(self.result['power_bi_desktop_runtime_executed'])
 def test_no_compiled_pbix_claim(self):self.assertFalse(self.result['actual_pbix_created'])

if __name__=='__main__':unittest.main()
