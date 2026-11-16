"""Create recruiter-ready Excel executive workbook using artifact_tool only."""
from __future__ import annotations
import csv,json
from pathlib import Path
from artifact_tool import Workbook, SpreadsheetFile
ROOT=Path(__file__).resolve().parents[1]
READ=lambda filename:list(csv.DictReader((ROOT/'data/marts'/filename).open(encoding='utf-8')))
monthly=READ('monthly.csv');causes=READ('root_causes.csv');vendors=READ('vendors.csv')[:30];cases=READ('sample_for_excel.csv')
metrics=json.loads((ROOT/'data/marts/metrics.json').read_text())
NAVY='#12213B'; DARK='#0B1628'; BLUE='#4F75FF'; TEAL='#19C9AD'; WHITE='#FFFFFF'; SMOKE='#EEF3F8'; LIGHT='#DCE6F1'; MUTED='#63748B'; RED='#E85C68'; YELLOW='#FFF0A7'; GREEN='#007D52'
CURRENCY='€#,##0;[Red](€#,##0);"–"'; NUMBER='#,##0;[Red](#,##0);"–"';PERCENT='0.0%;[Red](0.0%);"–"'
w=Workbook.create()
for name in ['Executive','Monthly Trend','Root Causes','Vendor Focus','Casebook','Scenario Lab','Methodology']:
    w.worksheets.add(name)

def sheet(name):return w.worksheets.get_item(name)
def merge_title(sh,rng,value,color=DARK,size=20):
    sh.merge_cells(rng)
    cell=sh.get_range(rng.split(':')[0]);cell.values=[[value]]
    rg=sh.get_range(rng);rg.format={'fill':color,'font':{'bold':True,'size':size,'color':WHITE},'row_height':36,'vertical_alignment':'center'}
def bar(sh,rng,title):
    sh.merge_cells(rng);sh.get_range(rng.split(':')[0]).values=[[title]]
    sh.get_range(rng).format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':11},'row_height':24}
def headers(sh,rng):
    sh.get_range(rng).format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':10},'row_height':24,'wrap_text':True,'vertical_alignment':'center'}
def base(sh,cols,rows=55):
    sh.get_range(f'A1:{cols}{rows}').format.row_height=21
    sh.get_range(f'A1:{cols}{rows}').format.font.name='Aptos'
    sh.get_range(f'A1:{cols}{rows}').format.font.size=10
    sh.get_range(f'A1:{cols}{rows}').format.column_width=14
    sh.get_range(f'A1:{cols}{rows}').format.font.color=NAVY

def values(sh, rng, vals):sh.get_range(rng).values=vals

# Monthly source: 22 monthly periods, one summary row per month.
sh=sheet('Monthly Trend');base(sh,'H',35)
merge_title(sh,'A1:H2','MONTHLY SPEND & EXPOSURE')
values(sh,'A3',[['Monthly transaction economics | all values in EUR | synthetic case study']])
header=['Month','Payments','Flagged','Spend (EUR)','Flag rate','Gross leakage (EUR)','Modeled recovery (EUR)','Leakage / spend']
sh.get_range('A5:H5').values=[header];headers(sh,'A5:H5')
rows=[]
for item in monthly:
    rows.append([item['payment_month'],int(item['payments']),int(item['flagged_payments']),float(item['spend_eur']),None,float(item['gross_loss_eur']),float(item['modeled_recovery_eur']),None])
sh.get_range(f'A6:H{5+len(rows)}').values=rows
for rr in range(6,6+len(rows)):
    sh.get_range(f'E{rr}').formulas=[[f'=IFERROR(C{rr}/B{rr},0)']]
    sh.get_range(f'H{rr}').formulas=[[f'=IFERROR(F{rr}/D{rr},0)']]
sh.get_range(f'D6:D{5+len(rows)}').set_number_format(CURRENCY)
sh.get_range(f'F6:G{5+len(rows)}').set_number_format(CURRENCY)
sh.get_range(f'E6:E{5+len(rows)}').set_number_format(PERCENT)
sh.get_range(f'H6:H{5+len(rows)}').set_number_format(PERCENT)
sh.get_range('A1:A28').format.column_width=16
sh.get_range('D1:D28').format.column_width=22
sh.get_range('F1:G28').format.column_width=23
sh.get_range('H1:H28').format.column_width=21
sh.get_range('B1:C28').format.column_width=13
sh.freeze_panes.freeze_rows(5)
sh.get_range('F6:F27').conditional_formats.add_data_bar({'color':BLUE,'gradient':False})

# Root causes
sh=sheet('Root Causes');base(sh,'H',32)
merge_title(sh,'A1:H2','LOSS DRIVERS | CONTROL TAXONOMY')
values(sh,'A3',[['Detected exceptions ≠ confirmed fraud. Recovery values are scenario estimates.']])
sh.get_range('A5:E5').values=[['Exception type','Payments','Gross loss (EUR)','Modeled recovery (EUR)','Rule confidence']];headers(sh,'A5:E5')
for idx,item in enumerate(causes,start=6):
    sh.get_range(f'A{idx}:E{idx}').values=[[item['issue_type'],int(item['flagged_payments']),float(item['gross_loss_eur']),float(item['modeled_recovery_eur']),float(item['rule_confidence'])]]
sh.get_range('A13').values=[['TOTAL']];sh.get_range('B13').formulas=[['=SUM(B6:B11)']]
sh.get_range('C13').formulas=[['=SUM(C6:C11)']];sh.get_range('D13').formulas=[['=SUM(D6:D11)']]
sh.get_range('A13:E13').format={'fill':SMOKE,'font':{'bold':True,'color':NAVY},'row_height':28}
sh.get_range('C6:D13').set_number_format(CURRENCY);sh.get_range('E6:E11').set_number_format(PERCENT)
sh.get_range('A1:A16').format.column_width=32;sh.get_range('C1:D16').format.column_width=24
sh.get_range('B1:B16').format.column_width=17;sh.get_range('E1:E16').format.column_width=22
sh.get_range('C6:C11').conditional_formats.add_data_bar({'color':TEAL,'gradient':True})

# Vendors
sh=sheet('Vendor Focus');base(sh,'H',42)
merge_title(sh,'A1:H2','TOP VENDOR EXPOSURES')
values(sh,'A3',[['Ranked by indicative gross leakage; investigate before contacting suppliers.']])
sh.get_range('A5:H5').values=[['Vendor ID','Vendor','Country','Category','Payments','Spend (EUR)','Gross loss (EUR)','Recovery (EUR)']];headers(sh,'A5:H5')
for rr,item in enumerate(vendors,start=6):
    sh.get_range(f'A{rr}:H{rr}').values=[[item['vendor_id'],item['vendor_name'],item['country'],item['category'],int(item['payments']),float(item['spend_eur']),float(item['gross_loss_eur']),float(item['modeled_recovery_eur'])]]
sh.get_range('F6:H35').set_number_format(CURRENCY)
sh.get_range('A1:A38').format.column_width=14
sh.get_range('B1:B38').format.column_width=39
sh.get_range('C1:C38').format.column_width=18
sh.get_range('D1:D38').format.column_width=23
sh.get_range('E1:E38').format.column_width=13
sh.get_range('F1:H38').format.column_width=22
sh.freeze_panes.freeze_rows(5)
sh.get_range('G6:G35').conditional_formats.add_data_bar({'color':RED,'gradient':True})

# Casebook: 400 top exceptions + real trace fields.
sh=sheet('Casebook');base(sh,'J',410)
merge_title(sh,'A1:J2','EVIDENCE CASEBOOK | TOP 400')
values(sh,'A3',[['Sorted by estimated gross loss; investigate originals, contracts, payment proofs and receipt evidence.']])
sh.get_range('A5:J5').values=[['Payment ID','Month','Vendor','Category','Country','Issue type','Gross loss (EUR)','Modeled recovery (EUR)','Confidence','Recommended next action']]
headers(sh,'A5:J5')
case_rows=[[c['payment_id'],c['payment_month'],c['vendor_name'],c['category'],c['country'],c['issue_type'],float(c['estimated_gross_loss_eur']),float(c['modeled_recovery_eur']),float(c['rule_confidence']),c['recommended_action']] for c in cases]
sh.get_range(f'A6:J{5+len(case_rows)}').values=case_rows
sh.get_range(f'G6:H{5+len(case_rows)}').set_number_format(CURRENCY)
sh.get_range(f'I6:I{5+len(case_rows)}').set_number_format(PERCENT)
for col,width in [('A',17),('B',14),('C',39),('D',24),('E',19),('F',28),('G',20),('H',22),('I',15),('J',59)]:
    sh.get_range(f'{col}1:{col}408').format.column_width=width
sh.freeze_panes.freeze_rows(5)
sh.tables.add(f'A5:J{5+len(case_rows)}',True,'AuditCases')

# Scenario lab: editable inputs separate from calculations
sh=sheet('Scenario Lab');base(sh,'H',35)
merge_title(sh,'A1:H2','RECOVERY SCENARIO LAB')
values(sh,'A3',[['Apply realistic realization levels to modeled recoverable amounts. Assumptions are editable blue cells.']])
bar(sh,'A5:E5','SCENARIO ASSUMPTIONS & RECOVERY')
sh.get_range('A6:C6').values=[['Scenario','Realization factor','Expected recovery (EUR)']]
headers(sh,'A6:C6')
for rr,scenario,factor in [(7,'Conservative',.5),(8,'Base case',.75),(9,'Optimistic',1)]:
    sh.get_range(f'A{rr}:B{rr}').values=[[scenario,factor]]
    sh.get_range(f'C{rr}').formulas=[[f"='Root Causes'!$D$13*B{rr}"]]
sh.get_range('B7:B9').set_number_format(PERCENT);sh.get_range('C7:C9').set_number_format(CURRENCY)
sh.get_range('B7:B9').format={'fill':YELLOW,'font':{'color':'#0000FF','bold':True},'row_height':28}
sh.get_range('C7:C9').format.font.color=GREEN
sh.get_range('A12:E12').merge_cells('A12:E12') if False else None
bar(sh,'A12:E12','DECISION RULES')
sh.get_range('A14:B19').values=[
 ['1','Validate payment + contract against authoritative systems'],
 ['2','Separate legal recoverability from technical anomaly'],
 ['3','Do not classify an approval bypass as a financial loss'],
 ['4','Apply supplier-specific haircut before recoverability'],
 ['5','Escalate only verified financial cases'],
 ['6','Track actual credits separately from scenario estimates'],
]
sh.get_range('A1:A28').format.column_width=16;sh.get_range('B1:B28').format.column_width=26
sh.get_range('C1:C28').format.column_width=30;sh.get_range('D1:E28').format.column_width=18
sh.get_range('B14:B19').format.column_width=75

# Landing / executive summary
sh=sheet('Executive');base(sh,'O',54)
sh.get_range('A1:O53').format.column_width=12
merge_title(sh,'A1:O3','PROFITLEAK ATLAS  /  FINANCIAL FORENSICS',size=23)
sh.merge_cells('A4:O4');sh.get_range('A4').values=[['Synthetic EU procurement audit | 220,000 payments | Contract, FX, duplicate and control-risk intelligence']]
sh.get_range('A4:O4').format={'fill':NAVY,'font':{'color':LIGHT,'size':10},'row_height':27}
for label_rng,val_rng,title,formula in [
 ('A6:D6','A7:D9','TOTAL PAYMENT SPEND (EUR)',"=SUM('Monthly Trend'!D6:D27)"),
 ('F6:I6','F7:I9','GROSS EXPOSURE (EUR)',"=SUM('Monthly Trend'!F6:F27)"),
 ('K6:N6','K7:N9','MODELED RECOVERY (EUR)',"=SUM('Monthly Trend'!G6:G27)"),
 ('A11:D11','A12:D14','FLAGGED PAYMENTS',"='Root Causes'!B13"),
 ('F11:I11','F12:I14','GROSS LOSS / SPEND',"=IFERROR(F7/A7,0)"),
 ('K11:N11','K12:N14','CONTROL-ONLY FLAGS',"='Root Causes'!B11")]:
    sh.merge_cells(label_rng);sh.get_range(label_rng.split(':')[0]).values=[[title]]
    sh.get_range(label_rng).format={'fill':NAVY,'font':{'bold':True,'color':LIGHT,'size':9},'row_height':21}
    sh.merge_cells(val_rng);sh.get_range(val_rng.split(':')[0]).formulas=[[formula]]
    sh.get_range(val_rng).format={'fill':SMOKE,'font':{'bold':True,'color':NAVY,'size':23},'row_height':28}
sh.get_range('A7').set_number_format(CURRENCY);sh.get_range('F7').set_number_format(CURRENCY);sh.get_range('K7').set_number_format(CURRENCY)
sh.get_range('A12').set_number_format(NUMBER);sh.get_range('F12').set_number_format(PERCENT);sh.get_range('K12').set_number_format(NUMBER)
bar(sh,'A16:G16','EXCEPTION BREAKDOWN');bar(sh,'I16:O16','RECOVERY DECISIONS')
sh.get_range('A18:D18').values=[['Loss type','Cases','Gross loss','Recovery']];headers(sh,'A18:D18')
for rr,root_row in enumerate(range(6,12),start=19):
    for col,orig_col in [('A','A'),('B','B'),('C','C'),('D','D')]:
        sh.get_range(f'{col}{rr}').formulas=[[f"='Root Causes'!{orig_col}{root_row}"]]
sh.get_range('C19:D24').set_number_format(CURRENCY)
sh.get_range('A18:A25').format.column_width=29
sh.get_range('C18:D25').format.column_width=18
sh.get_range('I18:O19').merge_cells('I18:O19') if False else None
sh.merge_cells('I18:O19');sh.get_range('I18').values=[['POTENTIAL ≠ RECOVERED CASH']]
sh.get_range('I18:O19').format={'fill':YELLOW,'font':{'bold':True,'color':NAVY,'size':13},'row_height':24}
for r,text in [(21,'① Validate contracts and original invoice evidence'),(23,'② Prioritize bank-verified duplicate settlements'),(25,'③ Confirm supplier credits before booking savings')]:
    sh.merge_cells(f'I{r}:O{r}');sh.get_range(f'I{r}').values=[[text]]
    sh.get_range(f'I{r}:O{r}').format={'fill':SMOKE,'font':{'color':NAVY,'size':10},'row_height':28}
bar(sh,'A28:G28','MONTHLY EXPOSURE TREND');bar(sh,'I28:O28','LOSS MIX BY ROOT CAUSE')
sh.merge_cells('A48:O49');sh.get_range('A48').values=[['IMPORTANT: Every financial result is simulated. Rule confidence is a designed scoring heuristic, not statistical calibration.']]
sh.get_range('A48:O49').format={'fill':SMOKE,'font':{'color':MUTED,'size':10},'row_height':22,'wrap_text':True}

# Methodology and traceability
sh=sheet('Methodology');base(sh,'H',28)
merge_title(sh,'A1:H2','MODEL CARD  /  AUDITABILITY')
content=[
 ('Data provenance','100% synthetic; generated in src/generate_data.py with fixed seed 20261115.'),
 ('Currency / scope','EUR procurement payments in fictional EU group, January 2025 – October 2026.'),
 ('Population','220,000 payment events; one payment row is the analytical grain.'),
 ('Detection','SQLite rules examine contract pricing, duplicates, receipts, FX, missed discounts and PO splits.'),
 ('Gross exposure','Potentially recoverable financial losses only; approval fragmentation is a risk flag with €0 leakage.'),
 ('Recovery estimate','Gross exposure × cause recovery probability × supplier-specific recovery haircut.'),
 ('Quality','Deterministic synthetics allow exact truth matching; metrics do NOT transfer to real-world data.'),
 ('Limitations','Contract effective dates, bank confirmations, VAT, vendor disputes and causal attribution are not modeled.'),
 ('Disclaimer','No detected case alone proves fraud, liability, or recoverability.'),
 ('Source', 'Project-authored synthetic data; README.md and docs/assumptions.md in this package.'),
]
for i,(key,value) in enumerate(content,start=5):
    sh.get_range(f'A{i}').values=[[key]];sh.merge_cells(f'B{i}:H{i}');sh.get_range(f'B{i}').values=[[value]]
    sh.get_range(f'A{i}').format={'fill':NAVY,'font':{'bold':True,'color':WHITE},'row_height':34}
    sh.get_range(f'B{i}:H{i}').format={'fill':SMOKE if i%2 else WHITE,'font':{'color':NAVY},'wrap_text':True,'row_height':34}
sh.get_range('A1:A22').format.column_width=28;sh.get_range('B1:H22').format.column_width=19

# Charts placed below tables/near dynamic summary blocks. Chart source is validated sheet data.
try:
    sh=sheet('Executive')
    c=sh.charts.add('line',{'title':'Gross leakage by month','has_legend':False})
    s=c.series.add('Estimated leakage');s.category_formula="'Monthly Trend'!$A$6:$A$27";s.formula="'Monthly Trend'!$F$6:$F$27";s.values_format_code='€#,##0'
    c.set_position('A30','H46')
    c2=sh.charts.add('bar',{'title':'Exception drivers','has_legend':False});c2.bar_options.direction='bar';c2.bar_options.grouping='clustered'
    s2=c2.series.add('Gross loss');s2.category_formula="'Root Causes'!$A$6:$A$11";s2.formula="'Root Causes'!$C$6:$C$11";s2.values_format_code='€#,##0'
    c2.set_position('I30','O46')
except Exception as err:
    print('Chart warning (workbook still usable):',err)

outfile=ROOT/'excel/ProfitLeak_Atlas_Executive.xlsx'
SpreadsheetFile.export_xlsx(w).save(str(outfile))
print('Workbook saved:',outfile)
try:
    print('Inspect:',w.inspect({'kind':'table','range':'Executive!A6:D14','include':'values,formulas','table_max_rows':10,'table_max_cols':4}).ndjson[:2000])
    print('Errors:',w.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':30}}).ndjson[:2000])
except Exception as e:print('Inspection warning:',e)
