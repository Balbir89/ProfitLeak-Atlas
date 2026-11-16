"""Reproducible, synthetic EU procurement dataset. Python standard library only."""
from __future__ import annotations
import argparse, csv, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=[('Cloud & Software',45),('Logistics',18),('Professional Services',76),('Facilities',14.5),('Packaging',6.5),('Marketing',39),('Hardware',33),('Utilities',24)]
COUNTRIES=['Germany','France','Netherlands','Italy','Spain','Poland','Belgium','Austria']
COST_CENTERS=['Operations','Commercial','Finance','Technology','Customer Success','Product']
MONTHS=[f'{year}-{month:02d}' for year in (2025,2026) for month in range(1,13) if not (year==2026 and month>10)]

def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def generate(n=220000,seed=20261115):
    r=random.Random(seed)
    vendors=[]; contracts=[]
    for i in range(1,281):
        category,base=CATEGORIES[(i*11)%len(CATEGORIES)]
        vendor_id=f'V{i:04d}'
        v={'vendor_id':vendor_id,'vendor_name':f'{["Atlas","Nova","Helix","Verde","Orion","Cedar","Apex"][i%7]} {category.split()[0]} Partners {i:03d}',
           'category':category,'country':COUNTRIES[(i*7+i//9)%len(COUNTRIES)], 'vendor_tier':['Strategic','Core','Occasional'][i%3]}
        vendors.append(v)
        price=round(base*r.uniform(.63,1.37),2)
        contracts.append({'vendor_id':vendor_id,'contract_id':f'C{i:04d}', 'contract_unit_price_eur':price,
          'early_discount_pct':[.015,.02,.025,.03][i%4], 'approval_threshold_eur':[600,900,1200,1500][i%4],
          'allowed_fx_spread_pct':.005,'recovery_haircut_pct':[.05,.1,.15][i%3]})
    vmap={v['vendor_id']:v for v in vendors}; cmap={c['vendor_id']:c for c in contracts}
    write_csv(ROOT/'data/master/vendors.csv', list(vendors[0]), vendors)
    write_csv(ROOT/'data/master/contracts.csv',list(contracts[0]),contracts)
    fields=['payment_id','invoice_ref','purchase_order','vendor_id','payment_month','cost_center','quantity','billed_unit_price_eur',
      'received_qty','paid_early','discount_taken_pct','fx_spread_pct','paid_amount_eur','approval_tier',
      'invoice_authorized_cents']
    truth_fields=['payment_id','injected_issue','synthetic_true_leakage_eur']
    raw_path=ROOT/'data/raw/payments.csv'; truth_path=ROOT/'data/truth/injected_labels.csv'
    raw_path.parent.mkdir(parents=True,exist_ok=True)
    truth_path.parent.mkdir(parents=True,exist_ok=True)
    seen=[]; issues={'No exception':0}
    with raw_path.open('w',newline='',encoding='utf-8') as raw_file,truth_path.open('w',newline='',encoding='utf-8') as truth_file:
        writer=csv.DictWriter(raw_file,fields);writer.writeheader()
        truth_writer=csv.DictWriter(truth_file,truth_fields);truth_writer.writeheader()
        i=1
        while i<=n:
            u=r.random()
            if u<.035 and seen: kind='Duplicate payment'
            elif u<.095: kind='Contract price variance'
            elif u<.137: kind='Missed early discount'
            elif u<.173: kind='FX spread excess'
            elif u<.190: kind='Undelivered goods'
            elif u<.218 and i<n: kind='Approval fragmentation'
            else: kind='No exception'
            if kind=='Duplicate payment':
                original=r.choice(seen)
                rec=original.copy();rec['payment_id']=f'P{i:07d}'
                leak=float(rec['paid_amount_eur'])
                # Duplicates deliberately carry the same invoice reference, PO and payment attributes.
                writer.writerow(rec);truth_writer.writerow({'payment_id':rec['payment_id'],'injected_issue':kind,'synthetic_true_leakage_eur':round(leak,2)})
                issues[kind]=issues.get(kind,0)+1;i+=1;continue
            v=vendors[r.randrange(len(vendors))];c=cmap[v['vendor_id']];qty=r.randint(2,42)
            actual_unit=float(c['contract_unit_price_eur']); base_price=actual_unit
            early=int(r.random()<.27);discount=float(c['early_discount_pct']) if early else 0.0
            spread=round(r.uniform(0,.004),4)
            received=qty; loss=0
            if kind=='Contract price variance':
                actual_unit=round(base_price*r.uniform(1.065,1.29),2)
                loss=(actual_unit-base_price)*qty
            elif kind=='Missed early discount':
                early=1;discount=0
                loss=base_price*qty*float(c['early_discount_pct'])
            elif kind=='FX spread excess':
                spread=round(r.uniform(.028,.088),4)
                loss=base_price*qty*(1-discount)*(spread-float(c['allowed_fx_spread_pct']))
            elif kind=='Undelivered goods':
                received=0;loss=base_price*qty*(1-discount)*(1+spread)
            month=r.choice(MONTHS)
            po=f'PO{i:07d}'
            if kind=='Approval fragmentation':
                # Two below-threshold payments on the same PO; risk flag but no assumed cash loss.
                threshold=float(c['approval_threshold_eur'])
                qty=max(1,round(threshold*.65/base_price))
                actual_unit=base_price
                early=0;discount=0;spread=0
                for j in range(2):
                    rec={'payment_id':f'P{i+j:07d}','invoice_ref':f'INV{i+j:07d}','purchase_order':po,
                         'vendor_id':v['vendor_id'],'payment_month':month,'cost_center':r.choice(COST_CENTERS),
                         'quantity':qty,'billed_unit_price_eur':actual_unit,'received_qty':qty,'paid_early':early,
                         'discount_taken_pct':discount,'fx_spread_pct':spread,'paid_amount_eur':round(qty*actual_unit,2),
                         'approval_tier':'Unapproved','invoice_authorized_cents':round(qty*actual_unit*100)}
                    writer.writerow(rec);truth_writer.writerow({'payment_id':rec['payment_id'],'injected_issue':kind,'synthetic_true_leakage_eur':0})
                    issues[kind]=issues.get(kind,0)+1
                i+=2;continue
            paid=round(qty*actual_unit*(1-discount)*(1+spread),2)
            rec={'payment_id':f'P{i:07d}','invoice_ref':f'INV{i:07d}','purchase_order':po,
                 'vendor_id':v['vendor_id'],'payment_month':month,'cost_center':r.choice(COST_CENTERS),
                 'quantity':qty,'billed_unit_price_eur':actual_unit,'received_qty':received,'paid_early':early,
                 'discount_taken_pct':discount,'fx_spread_pct':spread,'paid_amount_eur':paid,
                 'approval_tier':'Standard' if paid<float(c['approval_threshold_eur']) else 'Approved',
                 'invoice_authorized_cents':round(paid*100)}
            writer.writerow(rec);truth_writer.writerow({'payment_id':rec['payment_id'],'injected_issue':kind,'synthetic_true_leakage_eur':round(loss,2)})
            if len(seen)<25000 and kind=='No exception':seen.append(rec.copy())
            issues[kind]=issues.get(kind,0)+1;i+=1
    print(f'Created {n:,} payments; issue profile: {issues}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rows',type=int,default=220000);p.add_argument('--seed',type=int,default=20261115)
    a=p.parse_args();generate(a.rows,a.seed)
