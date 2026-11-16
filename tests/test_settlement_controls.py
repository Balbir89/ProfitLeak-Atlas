from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
from threading import Barrier
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import build_pipeline
import case_workflow as workflow
from validate_settlements import INSERT_PAYMENT, run, settlement_db


class TestInvoiceSettlements(unittest.TestCase):
    def run_invoice(self, rows):
        with closing(settlement_db()) as conn:
            conn.executemany(INSERT_PAYMENT, [(pid, 'INV-1', 'PO-1', month, amount, cents)
                for pid, month, amount, cents in rows])
            return conn.execute('''SELECT payment_id,issue_type,estimated_gross_loss_eur
                FROM vw_cases ORDER BY payment_month,payment_id''').fetchall()

    def test_legitimate_installments_stay_within_invoice_total(self):
        rows = [('P1', '2026-01', 75, 20000), ('P2', '2026-02', 125, 20000)]
        self.assertEqual(self.run_invoice(rows), [('P1', 'No exception', 0), ('P2', 'No exception', 0)])

    def test_only_incremental_excess_counts_in_chronological_order(self):
        rows = [('P9', '2026-01', 100, 12500), ('P1', '2026-02', 70, 12500),
                ('P2', '2026-02', 30, 12500)]
        self.assertEqual(self.run_invoice(rows), [('P9', 'No exception', 0),
            ('P1', 'Duplicate payment', 45), ('P2', 'Duplicate payment', 30)])

    def test_money_math_uses_cents(self):
        rows = [('P1', '2026-01', 0.20, 30), ('P2', '2026-02', 0.11, 30)]
        self.assertEqual(self.run_invoice(rows)[1], ('P2', 'Duplicate payment', 0.01))

    def test_missing_or_conflicting_evidence_is_review_only(self):
        for totals in [(None, None), (10000, None), (10000, 12000)]:
            with self.subTest(totals=totals):
                rows = [('P1', '2026-01', 100, totals[0]), ('P2', '2026-02', 100, totals[1])]
                self.assertEqual(self.run_invoice(rows)[1], ('P2', 'Invoice repeat review', 0))

    def test_legacy_csv_optional_column_is_loaded_as_null(self):
        with tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as conn:
            path = Path(tmp) / 'legacy.csv'
            path.write_text('key\nA\n', encoding='utf-8')
            conn.execute('CREATE TABLE test(key TEXT, invoice_authorized_cents INT)')
            build_pipeline.import_csv(conn, 'test', path, ['key', 'invoice_authorized_cents'],
                {'invoice_authorized_cents': int}, optional=('invoice_authorized_cents',))
            self.assertEqual(conn.execute('SELECT * FROM test').fetchone(), ('A', None))

    def test_separate_settlement_challenge(self):
        stats = run(repetitions=15)
        result = stats['authorization_aware_rule']
        self.assertEqual((result['tp'], result['fp'], result['fn']), (60, 0, 0))
        self.assertEqual(result['absolute_exposure_error_eur'], 0)
        self.assertEqual(stats['repeat_only_baseline']['fp'], 45)
        self.assertEqual(stats['ambiguous_follow_up_reviews'], 30)
        self.assertEqual(stats['ambiguous_exposure_eur'], 0)


class TestCashCreditControls(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / 'workflow.db'
        self.case = 'EXAMPLE'
        with closing(workflow.connect(self.db)) as conn, conn:
            conn.executescript(workflow.DDL)
            conn.execute('''INSERT INTO audit_case (payment_id,issue_type,vendor_id,financial_exposure_eur,
                modeled_recovery_eur,priority_score,created_at,updated_at) VALUES (?, 'Duplicate payment',
                'V1',2.01,1,75,'2026-01-01','2026-01-01')''', (self.case,))
        workflow.transition(self.case, 'In Review', 'QA', 'Review started', self.db)
        workflow.add_evidence(self.case, 'demo://bank', 'Supporting statement', 'QA', self.db)
        workflow.transition(self.case, 'Verified', 'QA', 'Statement verified', self.db)

    def credit(self, amount, reference='demo://credit'):
        workflow.record_cash(self.case, amount, 'QA', reference, self.db)

    def balance_and_events(self):
        with closing(workflow.connect(self.db)) as conn:
            return conn.execute('''SELECT recovered_cash_eur,
                (SELECT COUNT(*) FROM audit_event WHERE action='CREDIT') FROM audit_case''').fetchone()[:]

    def test_retried_reference_after_closure_does_not_repeat_credit(self):
        self.credit('2.01')
        workflow.transition(self.case, 'Closed', 'QA', 'Statement reconciled', self.db)
        self.credit('2.010', ' demo://credit ')
        self.assertEqual(self.balance_and_events(), (2.01, 1))

    def test_changed_amount_on_existing_reference_is_rejected(self):
        self.credit('1.00')
        with self.assertRaisesRegex(ValueError, 'different amount'):
            self.credit('1.01')
        self.assertEqual(self.balance_and_events(), (1, 1))

    def test_concurrent_retry_records_only_one_event(self):
        barrier = Barrier(2)
        def submit():
            barrier.wait(timeout=5)
            self.credit('0.77')
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = [pool.submit(submit) for _ in range(2)]
            for attempt in pending:
                attempt.result()
        self.assertEqual(self.balance_and_events(), (0.77, 1))

    def test_rejects_non_finite_subcent_and_overage_values(self):
        for value in ('NaN', 'Infinity', '0.009', '2.02'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.credit(value)
        self.assertEqual(self.balance_and_events(), (0, 0))

    def test_existing_credit_event_remains_idempotent(self):
        with closing(workflow.connect(self.db)) as conn, conn:
            conn.execute('UPDATE audit_case SET recovered_cash_eur=1 WHERE payment_id=?', (self.case,))
            workflow.add_event(conn, self.case, 'CREDIT', '0.0', '1.0', 'QA', 'Cash evidence: demo://credit')
        self.credit('1.00')
        self.assertEqual(self.balance_and_events(), (1, 1))

    def test_audit_event_updates_and_deletes_are_blocked(self):
        with closing(workflow.connect(self.db)) as conn:
            for statement in ('UPDATE audit_event SET actor=\'changed\'', 'DELETE FROM audit_event'):
                with self.assertRaisesRegex(sqlite3.IntegrityError, 'append-only'):
                    conn.execute(statement)
