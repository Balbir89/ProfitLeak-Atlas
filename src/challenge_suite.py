"""Out-of-sample synthetic challenge: overt/subtle anomalies + legitimate large payments.

This is an intentionally difficult, separately generated scenario benchmark; never
call it a real-world fraud accuracy test. Labels are accessed only after scoring.
"""
import csv, json, math, random, sqlite3, statistics
from pathlib import Path
from risk_layer import ROOT,DB,robust_stats,robust_z,TRAIN_END

def evaluate(seed=2187, db=DB, root=ROOT):
    conn=sqlite3.connect(db)
    cohorts={}
    for category,value in conn.execute("SELECT category,paid_amount_eur FROM case_mart WHERE payment_month<=? AND issue_type='No exception'",(TRAIN_END,)):
        cohorts.setdefault(category,[]).append(value)
    conn.close()
    baseline={c:robust_stats(vals)[:2] for c,vals in cohorts.items()}
    rng=random.Random(seed);items=[];catnames=sorted(baseline)
    for i in range(1500):
        cat=catnames[i%len(catnames)]
        if i%31==0: tag,z='Injected obvious anomaly',rng.uniform(5.0,6.8)
        elif i%29==0:tag,z='Injected subtle anomaly',rng.uniform(1.7,3.2)
        elif i%27==0:tag,z='Legitimate high-value order',rng.uniform(5.1,6.7)
        else:tag,z='Normal payment',rng.gauss(0,.85)
        med,scale=baseline[cat]
        amount=round(math.expm1(med+z*scale),2)
        # Predict first. Then use the separate scenario labels for diagnostic reporting.
        scored_z=robust_z(amount,med,scale)
        flagged=scored_z>4.5
        truth=tag.startswith('Injected')
        items.append({'case_id':f'CH{i:05d}','category':cat,'amount_eur':amount,
          'category_robust_z':round(scored_z,3),'scenario_label':tag,'synthetic_anomaly':int(truth),'statistical_flag':int(flagged)})
    tp=sum(x['statistical_flag'] and x['synthetic_anomaly'] for x in items)
    fp=sum(x['statistical_flag'] and not x['synthetic_anomaly'] for x in items)
    fn=sum(not x['statistical_flag'] and x['synthetic_anomaly'] for x in items)
    tn=len(items)-tp-fp-fn
    metrics={'dataset':'Independent synthetic challenge: 1,500 constructed payments',
      'challenge_cases':len(items),'true_positive':tp,'false_positive':fp,'false_negative':fn,'true_negative':tn,
      'precision':round(tp/(tp+fp),4),'recall':round(tp/(tp+fn),4),
      'false_positive_rate':round(fp/(fp+tn),4),'threshold_robust_z':4.5,
      'warning':'Scenario diagnostics, not externally validated fraud/production accuracy. Legitimate high-value payments intentionally create false positives; subtle anomalies are missed.'}
    folder=Path(root)/'data/marts';folder.mkdir(parents=True,exist_ok=True)
    (folder/'challenge_validation.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
    with (folder/'challenge_cases.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(items[0]));writer.writeheader();writer.writerows(items)
    print(json.dumps(metrics,indent=2));return metrics
if __name__=='__main__':evaluate()
