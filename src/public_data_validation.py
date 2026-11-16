"""Independent, non-accusatory public vendor-payments data compatibility check.

Official source: https://data.cityofchicago.org/resource/s4vu-giwb.json
Default: small curated *real* records from the source, NOT representative.
Optional `--live`: download a fresh 2025-26 extract with standard-library urllib.
Neither path contains investigator-confirmed labels or contractual price/receipt data;
no recovery, model accuracy, or fraud conclusion is possible.
"""
from __future__ import annotations
import argparse, csv, json, re, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/public'
URL = 'https://data.cityofchicago.org/resource/s4vu-giwb.json'
DATE_RE = re.compile(r'^\d{2}/\d{2}/\d{4}$')
YEAR_RE = re.compile(r'^\d{4}$')

def fetch_live(limit=5000):
    if not 1 <= limit <= 10000: raise ValueError('Live limit must be 1..10000')
    # SODA unfiltered sample. Never imply random representativeness.
    query = urllib.parse.urlencode({'$limit': limit})
    req = urllib.request.Request(URL+'?'+query, headers={'User-Agent':'ProfitLeak-Atlas-Research/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=50) as response:
        raw = response.read(8_000_001)
    if len(raw)>8_000_000: raise ValueError('Response unexpectedly large')
    items = json.loads(raw)
    if not isinstance(items,list): raise ValueError('Unexpected public API response')
    return items

def scan(rows):
    inspected=0; itemized=0; rolled_up=0; invalid=0; dv=0
    total=Decimal('0'); exact_signatures=Counter(); voucher_groups=defaultdict(set)
    supplier_totals=defaultdict(lambda:Decimal('0'))
    review=[]
    for n,r in enumerate(rows):
        inspected += 1
        try:
            amt=Decimal(str(r['amount']))
            if not amt.is_finite(): raise InvalidOperation()
            vendor=str(r['vendor_name']).strip()
            if not vendor: raise ValueError('missing vendor')
        except (KeyError,ValueError,InvalidOperation,TypeError):
            invalid += 1;continue
        total += amt; supplier_totals[vendor]+=amt
        date=str(r.get('check_date',''))
        v=str(r.get('voucher_number','')).strip()
        contract=str(r.get('contract_number','')).strip()
        if DATE_RE.fullmatch(date):
            try:datetime.strptime(date,'%m/%d/%Y')
            except ValueError:invalid += 1;continue
            itemized += 1
            if contract=='DV': dv+=1
            # Strict repeated *full* row is a data-quality review candidate,
            # not proof that two independent payments occurred.
            if v and v!='Multiple':
                exact_signatures[(v,date,vendor,str(amt))]+=1
                voucher_groups[v].add((vendor,str(amt),date))
        elif YEAR_RE.fullmatch(date):
            rolled_up += 1
        else:
            invalid += 1
    exact_repeats=sum(count-1 for count in exact_signatures.values() if count>1)
    reused_voucher=sum(1 for s in voucher_groups.values() if len(s)>1)
    for (voucher,date,vendor,amount),count in sorted(exact_signatures.items()):
        if count>1:
            review.append({'review_type':'REPEATED_PUBLIC_ROW','voucher':voucher,'vendor':vendor,'check_date':date,'amount_usd':amount,'records':count,'fraud_confirmed':False})
    return {
        'publisher':'City of Chicago', 'dataset_id':'s4vu-giwb',
        'source_url':URL,'currency':'USD','records_inspected':inspected,
        'itemized_date_rows':itemized,'year_only_aggregate_rows':rolled_up,
        'invalid_or_missing_rows':invalid,'direct_voucher_rows':dv,
        'distinct_vendors':len(supplier_totals),'sum_of_selected_amounts_usd':str(total),
        'strict_duplicate_row_candidates':exact_repeats,
        'reused_voucher_across_distinct_details_candidates':reused_voucher,
        'confirmed_fraud_cases':None,'validated_fraud_precision':None,
        'recoverable_loss_usd':None,
        'limitations':[
            'The public extract includes year-only aggregated rows; these are not individual payments.',
            'Voucher reuse or same-value payments may be legitimate; double-payment assertions require bank/invoice evidence.',
            'No supplier contract terms, receipt records, approval thresholds, or verified case outcome labels are provided.',
            'This evaluates real-data ingestion and review controls only, not fraud-prediction accuracy or recovered cash.'
        ]
    },review

def build(live=False, limit=1000):
    DATA.mkdir(parents=True,exist_ok=True)
    if live:
        records=fetch_live(limit)
        kind='live_public_api_first_rows'
        (DATA/'chicago_live_response.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    else:
        records=json.loads((DATA/'chicago_vendor_payments_observed.json').read_text(encoding='utf-8'))['records']
        kind='curated_real_public_records'
    metrics,cases=scan(records)
    metrics['sample_kind']=kind
    metrics['representative_sample']=False
    metrics['all_public_record_values_genuinely_published']=True
    metrics['powerbi_real_data_is_loaded_in_current_snapshot']=False
    (DATA/'external_validation_results.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
    with (DATA/'public_payment_review_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['review_type','voucher','vendor','check_date','amount_usd','records','fraud_confirmed'])
        w.writeheader();w.writerows(cases)
    print(json.dumps(metrics,indent=2))
    return metrics

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',help='Fetch live public City of Chicago payments API data')
    parser.add_argument('--limit',type=int,default=1000)
    args=parser.parse_args()
    build(args.live,args.limit)
