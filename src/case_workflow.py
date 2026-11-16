"""Auditable, local SQLite case management for fictional transaction investigations.

Use `python src/case_workflow.py --help`. Actions are transactions with append-only
history and documented evidence references, not verified supplier credit recoveries.
"""
from __future__ import annotations
import argparse,csv,datetime,json,sqlite3
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/audit_workflow.db'
SOURCE=ROOT/'database/atlas.db'
STATUS={'New','In Review','Evidence Requested','Verified','Rejected','Recovery Pending','Closed'}
TRANSITIONS={
 'New':{'In Review','Rejected'},
 'In Review':{'Evidence Requested','Verified','Rejected'},
 'Evidence Requested':{'In Review','Rejected'},
 'Verified':{'Recovery Pending','Closed'},
 'Recovery Pending':{'In Review','Closed'},
 'Rejected':{'Closed'},
 'Closed':set(),
}
DDL='''PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS audit_case (
 payment_id TEXT PRIMARY KEY, issue_type TEXT NOT NULL,
 vendor_id TEXT NOT NULL, financial_exposure_eur REAL NOT NULL,
 modeled_recovery_eur REAL NOT NULL, priority_score REAL NOT NULL,
 status TEXT NOT NULL DEFAULT 'New', owner TEXT NOT NULL DEFAULT 'Unassigned',
 recovered_cash_eur REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL, CHECK(financial_exposure_eur>=0),CHECK(recovered_cash_eur>=0)
);
CREATE TABLE IF NOT EXISTS evidence (
 evidence_id INTEGER PRIMARY KEY AUTOINCREMENT, payment_id TEXT NOT NULL REFERENCES audit_case(payment_id),
 evidence_ref TEXT NOT NULL,description TEXT NOT NULL,submitted_by TEXT NOT NULL,created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_event (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT,payment_id TEXT NOT NULL REFERENCES audit_case(payment_id),
 action TEXT NOT NULL,previous_value TEXT,new_value TEXT NOT NULL,
 actor TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_events_case ON audit_event(payment_id,event_id);
CREATE INDEX IF NOT EXISTS idx_audit_credit_reference ON audit_event(payment_id,reason) WHERE action='CREDIT';
CREATE INDEX IF NOT EXISTS idx_audit_cases_status ON audit_case(status,priority_score);
CREATE TRIGGER IF NOT EXISTS audit_event_no_update BEFORE UPDATE ON audit_event
BEGIN SELECT RAISE(ABORT,'Audit history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_event_no_delete BEFORE DELETE ON audit_event
BEGIN SELECT RAISE(ABORT,'Audit history is append-only'); END;
'''
def now():return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
def connect(db=DB):
    conn=sqlite3.connect(db);conn.execute('PRAGMA foreign_keys=ON');conn.row_factory=sqlite3.Row;return conn
def add_event(conn,payment_id,action,before,after,actor,reason):
    conn.execute('INSERT INTO audit_event(payment_id,action,previous_value,new_value,actor,reason,created_at) VALUES (?,?,?,?,?,?,?)',
       (payment_id,action,before,after,actor,reason,now()))
def init(db=DB,source=SOURCE):
    src=sqlite3.connect(source);src.row_factory=sqlite3.Row
    conn=connect(db)
    try:
        conn.executescript(DDL)
        conn.execute('BEGIN IMMEDIATE')
        # Mostly high-priority financial cases, plus explicit zero-euro control cases.
        rows=src.execute('''SELECT r.payment_id,r.issue_type,r.vendor_id,r.financial_exposure_eur,
          r.modeled_recovery_eur,r.priority_score FROM risk_scores r WHERE r.issue_type<>'No exception'
          ORDER BY CASE WHEN r.financial_exposure_eur>0 THEN 0 ELSE 1 END, r.priority_score DESC, r.financial_exposure_eur DESC LIMIT 180''').fetchall()
        ctrl=src.execute('''SELECT payment_id,issue_type,vendor_id,financial_exposure_eur,modeled_recovery_eur,priority_score
          FROM risk_scores WHERE issue_type='Approval fragmentation' ORDER BY priority_score DESC LIMIT 20''').fetchall()
        for x in list(rows)+list(ctrl):
            existing=conn.execute('SELECT 1 FROM audit_case WHERE payment_id=?',(x['payment_id'],)).fetchone()
            if existing:continue
            conn.execute('''INSERT INTO audit_case(payment_id,issue_type,vendor_id,financial_exposure_eur,
              modeled_recovery_eur,priority_score,status,owner,created_at,updated_at)
              VALUES (?,?,?,?,?,?,'New','Unassigned',?,?)''',
              tuple(x)+(now(),now()))
            add_event(conn,x['payment_id'],'CREATE',None,'New','System','Synthetic case record generated from risk priority')
        conn.commit();return conn.execute('SELECT COUNT(*) FROM audit_case').fetchone()[0]
    finally:src.close();conn.close()
def require_case(conn,case):
    row=conn.execute('SELECT * FROM audit_case WHERE payment_id=?',(case,)).fetchone()
    if row is None:raise ValueError('Unknown payment_id '+case)
    return row
def assign(case,owner,actor,reason='',db=DB):
    if not owner.strip() or not actor.strip():raise ValueError('Owner and actor are required')
    with closing(connect(db)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row=require_case(conn,case)
        conn.execute('UPDATE audit_case SET owner=?,updated_at=? WHERE payment_id=?',(owner,now(),case))
        add_event(conn,case,'ASSIGN',row['owner'],owner,actor,reason or 'Owner assignment')
def add_evidence(case,reference,description,actor,db=DB):
    if not reference.strip() or not description.strip() or not actor.strip():raise ValueError('Evidence reference, description, actor are required')
    with closing(connect(db)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        require_case(conn,case)
        conn.execute('INSERT INTO evidence(payment_id,evidence_ref,description,submitted_by,created_at) VALUES (?,?,?,?,?)',
          (case,reference,description,actor,now()))
        add_event(conn,case,'EVIDENCE',None,reference,actor,description)
def transition(case,new_status,actor,reason,db=DB):
    if new_status not in STATUS:raise ValueError('Invalid status')
    if not reason.strip() or not actor.strip():raise ValueError('Actor and reason are required')
    with closing(connect(db)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row=require_case(conn,case)
        old=row['status']
        if new_status not in TRANSITIONS[old]:raise ValueError(f'Invalid status transition {old} -> {new_status}')
        evidence_count=conn.execute('SELECT COUNT(*) FROM evidence WHERE payment_id=?',(case,)).fetchone()[0]
        if new_status in ('Verified','Recovery Pending') and not evidence_count:
            raise ValueError('Verification or recovery requires referenced evidence')
        if new_status=='Closed' and old!='Rejected' and not evidence_count:
            raise ValueError('Closing a verified case requires evidence')
        if new_status=='Closed' and old=='Recovery Pending' and row['financial_exposure_eur']>0 and row['recovered_cash_eur']==0:
            raise ValueError('For expected monetary recovery, record cash credit or route back to review before closure')
        conn.execute('UPDATE audit_case SET status=?,updated_at=? WHERE payment_id=?',(new_status,now(),case))
        add_event(conn,case,'STATUS',old,new_status,actor,reason)
def record_cash(case,amount,actor,reference,db=DB):
    try:
        amount=Decimal(str(amount))
        valid=amount.is_finite() and amount>0 and amount==amount.quantize(Decimal('0.01'))
    except InvalidOperation:
        valid=False
    if not valid or not reference.strip() or not actor.strip():
        raise ValueError('Positive cash amount in whole cents, actor and verified credit reference required')
    reason='Cash evidence: '+reference.strip()
    with closing(connect(db)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row=require_case(conn,case)
        prior=conn.execute('''SELECT previous_value,new_value FROM audit_event
            WHERE payment_id=? AND action='CREDIT' AND reason=? ORDER BY event_id LIMIT 1''',(case,reason)).fetchone()
        if prior is not None:
            previous=Decimal(prior['previous_value']).quantize(Decimal('0.01'))
            recorded=Decimal(prior['new_value']).quantize(Decimal('0.01'))
            if recorded-previous!=amount:
                raise ValueError('Credit reference is already recorded with a different amount')
            return
        if row['status'] not in ('Verified','Recovery Pending'):raise ValueError('Verify before recording recovered cash')
        if row['financial_exposure_eur']<=0:raise ValueError('Cannot credit a control-only issue')
        current=Decimal(str(row['recovered_cash_eur'])).quantize(Decimal('0.01'))
        updated=current+amount
        if updated>Decimal(str(row['financial_exposure_eur'])):
            raise ValueError('Cash credits cannot exceed modeled gross exposure')
        if conn.execute('SELECT COUNT(*) FROM evidence WHERE payment_id=?',(case,)).fetchone()[0]<1:
            raise ValueError('Cash credit requires case evidence')
        conn.execute('UPDATE audit_case SET recovered_cash_eur=?,updated_at=? WHERE payment_id=?',(str(updated),now(),case))
        add_event(conn,case,'CREDIT',str(current),str(updated),actor,reason)
def export(db=DB,folder=None):
    folder=Path(folder or ROOT/'data/marts');folder.mkdir(parents=True,exist_ok=True)
    with closing(connect(db)) as conn, conn:
        conn.execute('BEGIN')
        for name,sql in [('audit_casebook.csv','''SELECT a.*, (SELECT COUNT(*) FROM evidence e WHERE e.payment_id=a.payment_id) AS evidence_count,
            (SELECT COUNT(*) FROM audit_event v WHERE v.payment_id=a.payment_id) AS event_count FROM audit_case a ORDER BY a.priority_score DESC'''),
            ('audit_events.csv','SELECT * FROM audit_event ORDER BY event_id'),
            ('audit_evidence.csv','SELECT * FROM evidence ORDER BY evidence_id')]:
            with (folder/name).open('w',newline='',encoding='utf8') as f:
                cur=conn.execute(sql);writer=csv.writer(f);writer.writerow([x[0] for x in cur.description]);writer.writerows(cur)
        summary={r['status']:r['n'] for r in conn.execute('SELECT status,count(*) n FROM audit_case GROUP BY status')}
        total=conn.execute('SELECT sum(recovered_cash_eur) FROM audit_case').fetchone()[0] or 0
        metrics={'status_counts':summary,'actual_cash_recovered_in_synthetic_demonstration_eur':round(total,2),
          'disclaimer':'Zero real-world recovery. Demo does not assert supplier confirmations.'}
        (folder/'workflow_status.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
        return metrics

def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DB)
    sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init');sub.add_parser('export')
    ap=sub.add_parser('assign');ap.add_argument('payment_id');ap.add_argument('owner');ap.add_argument('--actor',required=True);ap.add_argument('--reason',default='')
    ap=sub.add_parser('evidence');ap.add_argument('payment_id');ap.add_argument('reference');ap.add_argument('description');ap.add_argument('--actor',required=True)
    ap=sub.add_parser('status');ap.add_argument('payment_id');ap.add_argument('status',choices=sorted(STATUS));ap.add_argument('--actor',required=True);ap.add_argument('--reason',required=True)
    ap=sub.add_parser('cash');ap.add_argument('payment_id');ap.add_argument('amount');ap.add_argument('reference');ap.add_argument('--actor',required=True)
    a=parser.parse_args()
    if a.cmd=='init':print('Case count:',init(a.db))
    elif a.cmd=='export':print(json.dumps(export(a.db),indent=2))
    elif a.cmd=='assign':assign(a.payment_id,a.owner,a.actor,a.reason,a.db)
    elif a.cmd=='evidence':add_evidence(a.payment_id,a.reference,a.description,a.actor,a.db)
    elif a.cmd=='status':transition(a.payment_id,a.status,a.actor,a.reason,a.db)
    elif a.cmd=='cash':record_cash(a.payment_id,a.amount,a.actor,a.reference,a.db)
if __name__=='__main__':cli()
