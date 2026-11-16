"""Leakage Atlas expert upgrade: *secondary* statistical risk signals.

This module never uses injected labels to fit scores. It uses the first 12 months
of normal-rule payments as a historical reference distribution and evaluates
later months as temporal holdout. Signals are prioritization aids, not fraud
probabilities, financial-loss estimates, or independently calibrated predictions.
"""
from __future__ import annotations
import csv, json, math, sqlite3, statistics
from collections import defaultdict, Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database/atlas.db'
TRAIN_END='2025-12'

def robust_stats(series):
    values=sorted(math.log1p(max(0.0,float(v))) for v in series)
    if not values:return 0.,1.,[]
    mid=statistics.median(values)
    mad=statistics.median(abs(v-mid) for v in values)
    return mid,max(mad*1.4826,0.13),values

def robust_z(value, med, scale):
    return (math.log1p(max(0.,float(value)))-med)/scale

def drift_psi(train,test,bins=10):
    """Historical deciles; descriptive shift, not performance deterioration."""
    if len(train)<bins or len(test)<bins:return 0.0
    ordered=sorted(train)
    cuts=[ordered[min(len(ordered)-1,round(len(ordered)*i/bins))] for i in range(1,bins)]
    def histogram(xs):
        result=[0]*bins
        for x in xs:
            j=0
            while j<bins-1 and x>cuts[j]:j+=1
            result[j]+=1
        return [(n+0.5)/(len(xs)+.5*bins) for n in result]
    return sum((b-a)*math.log(b/a) for a,b in zip(histogram(train),histogram(test)))

def score_payment(issue, rule_conf, rz, vendor_rate):
    """Monotonic, bounded *heuristic* score; no claimed probability calibration."""
    rule={'No exception':0.,'Approval fragmentation':.58,'Invoice repeat review':.58}.get(issue,1.)
    dev=max(0.,min(1.,(rz-1.5)/5.5))
    v=min(1.,max(0.,vendor_rate)/.45)
    conf=max(0.,min(1.,float(rule_conf))) if issue!='No exception' else 0.
    return min(100.,round(52*rule+26*dev+12*v+10*conf,1))

def build(db=DB, output_root=ROOT):
    db=Path(db);output_root=Path(output_root)
    conn=sqlite3.connect(db)
    conn.row_factory=sqlite3.Row
    try:
        # Build historic references without looking at injected synthetic truth.
        training=defaultdict(list)
        vendor_total=Counter();vendor_flagged=Counter()
        for row in conn.execute("SELECT category,vendor_id,paid_amount_eur,issue_type FROM case_mart WHERE payment_month<=?",(TRAIN_END,)):
            vendor_total[row['vendor_id']]+=1
            if row['issue_type']!='No exception':vendor_flagged[row['vendor_id']]+=1
            if row['issue_type']=='No exception':training[row['category']].append(row['paid_amount_eur'])
        baselines={k:robust_stats(v) for k,v in training.items()}
        if not baselines: raise RuntimeError('No historical normal-rule payment sample')
        conn.executescript('''DROP TABLE IF EXISTS risk_scores;
            CREATE TABLE risk_scores(
            payment_id TEXT PRIMARY KEY, payment_month TEXT NOT NULL, vendor_id TEXT NOT NULL,
            category TEXT NOT NULL, issue_type TEXT NOT NULL, peer_robust_z REAL NOT NULL,
            historic_vendor_exception_rate REAL NOT NULL, priority_score REAL NOT NULL,
            priority_band TEXT NOT NULL, signal_explanation TEXT NOT NULL,
            financial_exposure_eur REAL NOT NULL, modeled_recovery_eur REAL NOT NULL,
            requires_review INTEGER NOT NULL);
            CREATE INDEX idx_risk_priority ON risk_scores(priority_score DESC);
            CREATE INDEX idx_risk_month ON risk_scores(payment_month);
            CREATE INDEX idx_risk_review ON risk_scores(requires_review,priority_score DESC);''')
        inserted=0;batch=[]
        test_values=defaultdict(list)
        counts=Counter();fp_only=0
        for c in conn.execute('''SELECT payment_id,payment_month,vendor_id,category,issue_type,
               rule_confidence,paid_amount_eur,estimated_gross_loss_eur,
               recovery_probability,recovery_haircut_pct FROM case_mart ORDER BY payment_id'''):
            name=c['category'];median,scale,_=baselines.get(name, (0.,1.,[]))
            z=robust_z(c['paid_amount_eur'],median,scale)
            rate=vendor_flagged[c['vendor_id']]/max(1,vendor_total[c['vendor_id']])
            score=score_payment(c['issue_type'],c['rule_confidence'],z,rate)
            band=('Critical' if score>=83 else 'High' if score>=65 else 'Medium' if score>=42 else 'Low')
            novel=(z>4.5 and c['issue_type']=='No exception')
            review=(c['issue_type']!='No exception' or novel)
            if novel:fp_only+=1
            drivers=[]
            if c['issue_type']!='No exception':drivers.append('Documented SQL review flag: '+c['issue_type'])
            if z>4.5:drivers.append('High payment size versus historic category peers')
            if rate>.28:drivers.append('Elevated historical vendor exception frequency')
            if not drivers:drivers=['No material screening trigger']
            rec=round(c['estimated_gross_loss_eur']*c['recovery_probability']*(1-c['recovery_haircut_pct']),2)
            batch.append((c['payment_id'],c['payment_month'],c['vendor_id'],name,c['issue_type'],round(z,3),round(rate,4),score,band,'; '.join(drivers),c['estimated_gross_loss_eur'],rec,int(review)))
            counts[band]+=1
            if c['payment_month']>TRAIN_END:test_values[name].append(math.log1p(max(0.,c['paid_amount_eur'])))
            inserted+=1
            if len(batch)==8000:
                conn.executemany('INSERT INTO risk_scores VALUES ('+','.join('?'*13)+')',batch);batch.clear()
        if batch:conn.executemany('INSERT INTO risk_scores VALUES ('+','.join('?'*13)+')',batch)
        conn.commit()
        summary={
          'model_type':'Robust category-normalized, rules-plus-behavioral review priority',
          'model_is_calibrated_probability':False,
          'historical_training_window':'2025-01 through '+TRAIN_END,
          'temporal_holdout_window':'2026-01 through 2026-10',
          'historical_normal_payments':sum(len(v) for v in training.values()),
          'scored_payments':inserted,
          'priority_bands':dict(counts),
          'rule_unflagged_statistical_reviews':fp_only,
          'category_psi':{k:round(drift_psi(baselines[k][2],test_values.get(k,[])),4) for k in sorted(baselines)},
          'limitation':'Synthetic, constructed data; these scores are NOT validated fraud probabilities. PSI shows distribution shift, not predictive accuracy.'
        }
        out=output_root/'data/marts';out.mkdir(parents=True,exist_ok=True)
        (out/'risk_model_validation.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
        with (out/'risk_priorities.csv').open('w',newline='',encoding='utf8') as f:
            cur=conn.execute('''SELECT r.payment_id, r.payment_month,r.vendor_id,c.vendor_name,r.category,r.issue_type,
                r.financial_exposure_eur,r.modeled_recovery_eur,r.priority_score,r.priority_band,
                r.peer_robust_z,r.historic_vendor_exception_rate,r.signal_explanation
                FROM risk_scores r JOIN case_mart c USING(payment_id) WHERE r.requires_review=1 ORDER BY r.priority_score DESC,r.financial_exposure_eur DESC''')
            writer=csv.writer(f);writer.writerow([x[0] for x in cur.description]);writer.writerows(cur)
        print(json.dumps(summary,indent=2))
        return summary
    finally:conn.close()
if __name__=='__main__':build()
