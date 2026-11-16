"""Extend existing dashboard with audit and validation operating sheets using artifact_tool."""
import csv,json
from pathlib import Path
from artifact_tool import Blob,SpreadsheetFile
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'excel/ProfitLeak_Atlas_Executive.xlsx'
OUT=ROOT/'excel/ProfitLeak_Atlas_Expert.xlsx'
NAVY='#14263D';STEEL='#223956';TEAL='#21B59A';GOLD='#F5C372';PALE='#EAF1F6';WHITE='#FFFFFF';RED='#C93C5B'
wb=SpreadsheetFile.import_xlsx(Blob.load(str(IN)))
val=json.loads((ROOT/'data/marts/risk_model_validation.json').read_text())
challenge=json.loads((ROOT/'data/marts/challenge_validation.json').read_text())
with (ROOT/'data/marts/audit_casebook.csv').open(newline='') as f:cases=list(csv.DictReader(f))

def title(sh,last,text):
    sh.merge_cells(f'A1:{last}2');sh.get_range('A1').values=[[text]]
    sh.get_range(f'A1:{last}2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':19},'row_height':24}
def head(sh,addr):
    sh.get_range(addr).format={'fill':STEEL,'font':{'bold':True,'color':WHITE,'size':10},'row_height':26}

sh=wb.worksheets.add('Risk Validation')
title(sh,'I','MODEL GOVERNANCE  |  OUT-OF-SAMPLE RISK CHECK')
sh.merge_cells('A3:I3');sh.get_range('A3').values=[['Rules flag potential issues; statistical signals prioritize reviews. Neither output establishes fraud or actual recoverability.']]
sh.get_range('A3:I3').format={'fill':PALE,'font':{'color':NAVY,'size':10},'row_height':30,'wrap_text':True}
sh.get_range('A5:D5').values=[['Diagnostic','Value','Scope','Interpretation']];head(sh,'A5:D5')
metrics=[
 ['Historical training records',val['historical_normal_payments'],'2025-01 to 2025-12','Normal-rule payments used for peer baseline'],
 ['Scored payment records',val['scored_payments'],'All 22 months','Heuristic prioritization, not calibrated probability'],
 ['Challenge records',challenge['challenge_cases'],'Independent synthetic','Newly constructed and separately labeled data'],
 ['Challenge precision',challenge['precision'],'Statistical signal only','False alarms intentionally present'],
 ['Challenge recall',challenge['recall'],'Statistical signal only','Missed subtle anomalies intentionally present'],
 ['False-positive rate',challenge['false_positive_rate'],'Challenge normal cases','High legitimate-value payments can be flagged'],
 ['True positives',challenge['true_positive'],'Constructed challenge','Correct alerts'],
 ['False positives',challenge['false_positive'],'Constructed challenge','Legitimate orders flagged'],
 ['False negatives',challenge['false_negative'],'Constructed challenge','Subtle anomalies missed'],
 ['True negatives',challenge['true_negative'],'Constructed challenge','Correct non-alerts']]
sh.get_range('A6:D15').values=metrics
sh.get_range('B9:B11').set_number_format('0.0%')
sh.get_range('A18:D18').values=[['Category','Historic-vs-holdout PSI','Indicative interpretation','Owner']];head(sh,'A18:D18')
psi=val['category_psi'];rows=[]
for k,v in psi.items():rows.append([k,v,'Descriptive drift only','Model Risk Team'])
sh.get_range(f'A19:D{18+len(rows)}').values=rows
sh.get_range(f'B19:B{18+len(rows)}').set_number_format('0.000')
sh.get_range(f'B19:B{18+len(rows)}').conditional_formats.add_data_bar({'color':TEAL,'gradient':False})
sh.get_range('A30:D30').values=[['MODEL CONTROL','Policy','Owner','Status']];head(sh,'A30:D30')
controls=[
 ['Holdout separation','Use prior-year category baselines','Analytics lead','Implemented'],
 ['Seed labels isolation','Do not use injection labels as predictor','Data engineer','Implemented'],
 ['Human review','Alerts are leads, not fraud determinations','Internal audit','Required'],
 ['Recovery accounting','Zero real cash recovered without credit evidence','Finance','Required'],
 ['Independent validation','External company data not available','Model risk','Open'],
 ['Power BI compatibility','PBIP source not tested in Windows Desktop','BI developer','Pending']]
sh.get_range('A31:D36').values=controls
sh.merge_cells('A39:I40');sh.get_range('A39').values=[['CRITICAL: Synthetic challenge precision/recall do not indicate production fraud-detection accuracy. Manual assessment and false-positive investigation are mandatory.']]
sh.get_range('A39:I40').format={'fill':'#FFF1DF','font':{'color':NAVY,'bold':True},'wrap_text':True,'row_height':28}
for c,w in [('A',32),('B',22),('C',40),('D',38)]:sh.get_range(f'{c}1:{c}42').format.column_width=w
sh.get_range('E1:I42').format.column_width=10
sh.freeze_panes.freeze_rows(5)

sh=wb.worksheets.add('Audit Workflow')
title(sh,'M','EVIDENCE LEDGER  |  CASE REVIEW QUEUE')
sh.merge_cells('A3:M3');sh.get_range('A3').values=[['Editable Owner, Status and Analyst Notes. This sheet does not automatically write back to the SQLite audit log; use the workflow CLI to persist changes.']]
sh.get_range('A3:M3').format={'fill':'#FFF1DF','font':{'color':NAVY},'wrap_text':True,'row_height':32}
columns=['Payment ID','Issue','Vendor','Gross exposure (€)','Modeled recovery (€)','Priority score','Status','Owner','Actual cash (€)','Evidence count','Event count','Analyst notes','Action required']
sh.get_range('A5:M5').values=[columns];head(sh,'A5:M5')
values=[]
for c in cases:
    values.append([c['payment_id'],c['issue_type'],c['vendor_id'],float(c['financial_exposure_eur']),float(c['modeled_recovery_eur']),float(c['priority_score']),c['status'],c['owner'],float(c['recovered_cash_eur']),int(c['evidence_count']),int(c['event_count']),'','Verify original invoice and supporting evidence'])
sh.get_range(f'A6:M{5+len(values)}').values=values
sh.get_range(f'D6:E{5+len(values)}').set_number_format('€#,##0.00')
sh.get_range(f'I6:I{5+len(values)}').set_number_format('€#,##0.00')
sh.get_range(f'F6:F{5+len(values)}').set_number_format('0.0')
sh.get_range(f'G6:G{5+len(values)}').data_validation={'rule':{'type':'list','values':['New','In Review','Evidence Requested','Verified','Rejected','Recovery Pending','Closed']}}
sh.get_range(f'F6:F{5+len(values)}').conditional_formats.add_data_bar({'color':RED,'gradient':False})
sh.get_range(f'A5:M{5+len(values)}').format.row_height=23
for c,w in [('A',17),('B',30),('C',16),('D',22),('E',23),('F',17),('G',24),('H',22),('I',20),('J',17),('K',17),('L',38),('M',46)]:sh.get_range(f'{c}1:{c}{8+len(values)}').format.column_width=w
sh.tables.add(f'A5:M{5+len(values)}',True,'ExpertAuditQueue')
sh.freeze_panes.freeze_rows(5)
try:
  check=wb.inspect({'kind':'table','range':'Risk Validation!A5:D11','include':'values,formulas','table_max_rows':7,'table_max_cols':4})
  print('INSPECT',check.ndjson[:1100])
except Exception as e: print('INSPECT WARNING',repr(e))
SpreadsheetFile.export_xlsx(wb).save(str(OUT))
print('EXPORTED',str(OUT),OUT.stat().st_size)
