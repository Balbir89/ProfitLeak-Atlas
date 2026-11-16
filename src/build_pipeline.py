"""SQLite analytics pipeline and quality gates. No third-party dependencies."""
from __future__ import annotations
import csv, sqlite3, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/atlas.db'

def import_csv(conn, table, filename, cols, types, optional=()):
    insert = 'INSERT INTO '+table+' ('+','.join(cols)+') VALUES ('+','.join('?'*len(cols))+')'
    with (ROOT/filename).open(newline='',encoding='utf-8') as f:
        reader=csv.reader(f)
        header=next(reader, [])
        positions={key: index for index, key in enumerate(header)}
        missing = set(cols) - positions.keys() - set(optional)
        if missing:
            raise ValueError(f'{filename} is missing columns: {", ".join(sorted(missing))}')
        fields=[(positions.get(key), types.get(key, str), key in optional) for key in cols]

        def read_rows():
            for row in reader:
                if not row:
                    continue
                if len(row)!=len(header):
                    raise ValueError(f'{filename}:{reader.line_num} has {len(row)} fields, expected {len(header)}')
                yield tuple(None if optional and (index is None or not row[index]) else convert(row[index])
                    for index, convert, optional in fields)

        conn.executemany(insert, read_rows())

def export_query(conn,sql,path):
    path.parent.mkdir(exist_ok=True,parents=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        cur=conn.execute(sql);writer=csv.writer(f);writer.writerow([x[0] for x in cur.description]);writer.writerows(cur)

def build():
    DB.parent.mkdir(exist_ok=True,parents=True)
    if DB.exists():DB.unlink()
    conn=sqlite3.connect(DB)
    try:
        conn.executescript((ROOT/'sql/01_schema.sql').read_text())
        import_csv(conn,'dim_vendor','data/master/vendors.csv',['vendor_id','vendor_name','category','country','vendor_tier'],{})
        import_csv(conn,'dim_contract','data/master/contracts.csv',
         ['vendor_id','contract_id','contract_unit_price_eur','early_discount_pct','approval_threshold_eur','allowed_fx_spread_pct','recovery_haircut_pct'],
         {x:float for x in ['contract_unit_price_eur','early_discount_pct','approval_threshold_eur','allowed_fx_spread_pct','recovery_haircut_pct']})
        import_csv(conn,'fact_payment','data/raw/payments.csv',
         ['payment_id','invoice_ref','purchase_order','vendor_id','payment_month','cost_center','quantity','billed_unit_price_eur','received_qty','paid_early','discount_taken_pct','fx_spread_pct','paid_amount_eur','approval_tier','invoice_authorized_cents'],
         {x:float for x in ['billed_unit_price_eur','discount_taken_pct','fx_spread_pct','paid_amount_eur']}|
         {x:int for x in ['quantity','received_qty','paid_early','invoice_authorized_cents']},
         optional=('invoice_authorized_cents',))
        conn.commit()
        conn.executescript((ROOT/'sql/02_detection.sql').read_text())
        conn.executescript((ROOT/'sql/03_marts.sql').read_text())
        # Materialize window result once to avoid re-running massive windows for every downstream query.
        conn.execute('CREATE TABLE case_mart AS SELECT * FROM vw_cases')
        conn.execute('CREATE UNIQUE INDEX idx_case_payment ON case_mart(payment_id)')
        conn.execute('CREATE INDEX idx_case_issue_month ON case_mart(issue_type,payment_month)')
        # Refresh marts to use materialized evidence for efficient dashboard queries.
        for view_name in ['mart_monthly','mart_root_causes','mart_vendors']:
            sql=conn.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name=?",(view_name,)).fetchone()[0]
            conn.execute('DROP VIEW '+view_name)
            conn.execute(sql.replace('FROM vw_cases','FROM case_mart'))
        exports={
          'monthly.csv':'SELECT * FROM mart_monthly',
          'root_causes.csv':'SELECT * FROM mart_root_causes',
          'vendors.csv':'SELECT * FROM mart_vendors',
          'cases.csv':"""SELECT payment_id,payment_month,vendor_id,vendor_name,category,country,cost_center,invoice_ref,purchase_order,issue_type,
                 paid_amount_eur,estimated_gross_loss_eur,recovery_probability,recovery_haircut_pct,rule_confidence,recommended_action,
                 ROUND(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct),2) AS modeled_recovery_eur,
                 authorized_cents AS verified_invoice_authorized_cents,paid_to_date_cents AS invoice_paid_to_date_cents
                 FROM case_mart WHERE issue_type<>'No exception' ORDER BY estimated_gross_loss_eur DESC""",
          'sample_for_excel.csv':"""SELECT payment_id,payment_month,vendor_name,category,country,issue_type,
                 estimated_gross_loss_eur,ROUND(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct),2) AS modeled_recovery_eur,
                 rule_confidence,recommended_action FROM case_mart WHERE issue_type<>'No exception' ORDER BY estimated_gross_loss_eur DESC LIMIT 400"""
        }
        for filename,query in exports.items(): export_query(conn,query,ROOT/'data/marts'/filename)
        # Ground truth isolated from detection pipeline; used *only* for backtest diagnostics.
        conn.execute('CREATE TABLE injected_truth (payment_id TEXT PRIMARY KEY, injected_issue TEXT, synthetic_true_leakage_eur REAL)')
        import_csv(conn,'injected_truth','data/truth/injected_labels.csv',['payment_id','injected_issue','synthetic_true_leakage_eur'],{'synthetic_true_leakage_eur':float})
        n=conn.execute('SELECT COUNT(*) FROM fact_payment').fetchone()[0]
        violations=conn.execute('SELECT COUNT(*) FROM case_mart WHERE estimated_gross_loss_eur<0').fetchone()[0]
        missing=conn.execute('SELECT COUNT(*) FROM fact_payment p LEFT JOIN case_mart c USING(payment_id) WHERE c.payment_id IS NULL').fetchone()[0]
        labels=conn.execute('SELECT COUNT(*) FROM injected_truth').fetchone()[0]
        assert n==labels and n>0 and violations==0 and missing==0,(n,labels,violations,missing)
        cm=conn.execute("""SELECT
          SUM(CASE WHEN c.issue_type=t.injected_issue THEN 1 ELSE 0 END) AS exact_matches,
          SUM(CASE WHEN c.issue_type<>'No exception' AND t.injected_issue<>'No exception' THEN 1 ELSE 0 END) AS tp,
          SUM(CASE WHEN c.issue_type<>'No exception' AND t.injected_issue='No exception' THEN 1 ELSE 0 END) AS fp,
          SUM(CASE WHEN c.issue_type='No exception' AND t.injected_issue<>'No exception' THEN 1 ELSE 0 END) AS fn
          FROM case_mart c JOIN injected_truth t USING(payment_id)""").fetchone()
        spend,loss,recovery=conn.execute('SELECT ROUND(SUM(paid_amount_eur),2),ROUND(SUM(estimated_gross_loss_eur),2),ROUND(SUM(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct)),2) FROM case_mart').fetchone()
        stats={'synthetic':True,'payments':n,'spend_eur':spend,'gross_estimated_loss_eur':loss,'modeled_recoverable_eur':recovery,
          'flagged_payments':conn.execute("SELECT COUNT(*) FROM case_mart WHERE issue_type<>'No exception'").fetchone()[0],
          'exact_label_accuracy':round(cm[0]/n,5),'binary_precision':round(cm[1]/(cm[1]+cm[2]),5) if cm[1]+cm[2] else 0,
          'binary_recall':round(cm[1]/(cm[1]+cm[3]),5) if cm[1]+cm[3] else 0,
          'warning':'Metrics describe constructed synthetic cases, not validated real-world fraud detection.'}
        (ROOT/'data/marts/metrics.json').write_text(json.dumps(stats,indent=2))
        conn.commit();print(json.dumps(stats,indent=2))
    finally:conn.close()

if __name__=='__main__':build()
