"""Create a self-contained Power BI PBIP/PBIR+TMDL *source* project.

The semantic model embeds a compact synthetic snapshot (not the 220k payment
population). Source format is checked structurally; requires Microsoft Power BI
Desktop on Windows for native validation and saving as .pbix.
"""
from __future__ import annotations
import csv, hashlib, json, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'powerbi/ProfitLeak_Atlas_PBIP'
PREFIX='https://developer.microsoft.com/json-schemas/fabric/'

def emit_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def stable_id(name):return hashlib.sha1(name.encode('utf8')).hexdigest()[:20]
def q(s):return '"'+str(s).replace('"','""').replace('\n',' ')+'"'
def m_literal(value, kind):
    if value is None or value=='':return 'null'
    if kind=='string':return q(value)
    if kind=='int64':return str(int(float(value)))
    return str(round(float(value),5))
def model_table(name, source_path, cols, limit=None, measures=None):
    rows=list(csv.DictReader((ROOT/source_path).open(newline='',encoding='utf8')))
    if limit:rows=rows[:limit]
    tmdl=['table '+name,'']
    for meas,formula,fmt in (measures or []):
        tmdl += [f"\tmeasure '{meas}' = {formula}",f'\t\tformatString: {fmt}','']
    for col,kind in cols:
        tmdl += ['\tcolumn '+col,f'\t\tdataType: {kind}',f'\t\tsourceColumn: {col}','\t\tsummarizeBy: none','']
    type_defs=', '.join(f'{col} = '+{'string':'text','double':'number','int64':'Int64.Type'}[kind] for col,kind in cols)
    tmdl += [f'\tpartition {name} = m','\t\tmode: import','\t\tsource =',f'\t\t\t#table(type table [{type_defs}], {{']
    for index,row in enumerate(rows):
        values=', '.join(m_literal(row[col],kind) for col,kind in cols)
        tmdl += [f'\t\t\t\t{{{values}}}'+(',' if index<len(rows)-1 else '')]
    tmdl += ['\t\t\t})','']
    emit=PROJECT/'ProfitLeak_Atlas.SemanticModel/definition/tables'/f'{name}.tmdl'
    emit.parent.mkdir(parents=True,exist_ok=True);emit.write_text('\n'.join(tmdl),encoding='utf8')
    return len(rows)

def projection(table,col,is_measure=False,active=False):
    field={'Measure' if is_measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}}
    z={'field':field,'queryRef':f'{table}.{col}','nativeQueryRef':col}
    if active:z['active']=True
    return z

def visual(page,name,kind,x,y,w,h,roles):
    vid=stable_id(page+'-'+name)
    p=PROJECT/'ProfitLeak_Atlas.Report/definition/pages'/page/'visuals'/vid/'visual.json'
    payload={'$schema':PREFIX+'item/report/definition/visualContainer/2.7.0/schema.json',
        'name':vid,'position':{'x':x,'y':y,'z':len(roles),'width':w,'height':h,'tabOrder':0},
        'visual':{'visualType':kind,'query':{'queryState':{k:{'projections':v} for k,v in roles.items()}},'drillFilterOtherVisuals':True}}
    emit_json(p,payload)

def build():
    name='ProfitLeak_Atlas'
    root=PROJECT
    root.mkdir(parents=True,exist_ok=True)
    emit_json(root/(name+'.pbip'),{'$schema':PREFIX+'pbip/pbipProperties/1.0.0/schema.json',
       'version':'1.0','artifacts':[{'report':{'path':name+'.Report'}}],'settings':{'enableAutoRecovery':True}})
    rep=root/(name+'.Report');model=root/(name+'.SemanticModel')
    emit_json(rep/'definition.pbir',{'$schema':PREFIX+'item/report/definitionProperties/2.0.0/schema.json',
      'version':'4.0','datasetReference':{'byPath':{'path':'../'+name+'.SemanticModel'}}})
    emit_json(model/'definition.pbism',{'$schema':PREFIX+'item/semanticModel/definitionProperties/1.0.0/schema.json',
      'version':'4.0','settings':{'qnaEnabled':False}})
    for base,kind in ((rep,'Report'),(model,'SemanticModel')):
        emit_json(base/'.platform',{'$schema':PREFIX+'gitIntegration/platformProperties/2.0.0/schema.json',
          'metadata':{'type':kind,'displayName':'ProfitLeak Atlas'},'config':{'version':'2.0','logicalId':str(uuid.uuid5(uuid.NAMESPACE_DNS,'profit-leak-atlas-'+kind))}})
    definition=model/'definition';definition.mkdir(exist_ok=True,parents=True)
    (definition/'database.tmdl').write_text('database ProfitLeakAtlas\n\tcompatibilityLevel: 1702\n\tcompatibilityMode: powerBI\n\tlanguage: 1033\n',encoding='utf8')
    tables={
      'Monthly':('data/marts/monthly.csv', [('payment_month','string'),('payments','int64'),('spend_eur','double'),('flagged_payments','int64'),('gross_loss_eur','double'),('modeled_recovery_eur','double')],None,
        [('Total Spend','SUM(Monthly[spend_eur])','€#,##0'),('Total Exposure','SUM(Monthly[gross_loss_eur])','€#,##0'),('Potential Recovery','SUM(Monthly[modeled_recovery_eur])','€#,##0'),('Screened Payments','SUM(Monthly[payments])','#,##0'),('Flagged Payments','SUM(Monthly[flagged_payments])','#,##0')]),
      'Causes':('data/marts/root_causes.csv',[('issue_type','string'),('flagged_payments','int64'),('gross_loss_eur','double'),('modeled_recovery_eur','double'),('rule_confidence','double')],None,[]),
      'Vendors':('data/marts/vendors.csv',[('vendor_id','string'),('vendor_name','string'),('country','string'),('category','string'),('payments','int64'),('spend_eur','double'),('flagged_payments','int64'),('gross_loss_eur','double'),('modeled_recovery_eur','double')],40,[]),
      'Audit':('data/marts/audit_casebook.csv',[('payment_id','string'),('issue_type','string'),('vendor_id','string'),('financial_exposure_eur','double'),('modeled_recovery_eur','double'),('priority_score','double'),('status','string'),('owner','string'),('recovered_cash_eur','double')],200,
           [('Cases In Queue','COUNTROWS(Audit)','#,##0'),('Verified Cases',"CALCULATE(COUNTROWS(Audit),Audit[status] = \"Verified\")",'#,##0')]),
    }
    n={table:model_table(table,*args) for table,args in tables.items()}
    (definition/'model.tmdl').write_text('model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\n'+ '\n'.join(f'ref table {t}' for t in tables)+'\n',encoding='utf8')
    (definition/'relationships.tmdl').write_text('',encoding='utf8')
    d=rep/'definition'
    emit_json(d/'version.json',{'$schema':PREFIX+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    emit_json(d/'report.json',{'$schema':PREFIX+'item/report/definition/report/3.2.0/schema.json'})
    pages=[('Executive Snapshot','01 · Executive intelligence'),('Financial Drivers','02 · Financial drivers'),('Case Operations','03 · Case operations')]
    ids=[stable_id(name) for name,label in pages]
    emit_json(d/'pages/pages.json',{'$schema':PREFIX+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':ids,'activePageName':ids[0]})
    for (orig,label),pid in zip(pages,ids):
        emit_json(d/'pages'/pid/'page.json',{'$schema':PREFIX+'item/report/definition/page/2.1.0/schema.json',
          'name':pid,'displayName':label,'displayOption':'FitToPage','height':720,'width':1280})
    a,b,c=ids
    for idx,measure in enumerate(['Total Spend','Total Exposure','Potential Recovery','Flagged Payments']):
        visual(a,measure,'cardVisual',24+316*idx,24,296,150,{'Data':[projection('Monthly',measure,True)]})
    visual(a,'Trend','lineChart',24,208,820,420,{'Category':[projection('Monthly','payment_month',active=True)],'Y':[projection('Monthly','gross_loss_eur')]})
    visual(a,'Causes','clusteredBarChart',868,208,390,420,{'Category':[projection('Causes','issue_type',active=True)],'Y':[projection('Causes','gross_loss_eur')]})
    visual(b,'Cause table','tableEx',24,22,690,590,{'Values':[projection('Causes',v) for v in ['issue_type','flagged_payments','gross_loss_eur','modeled_recovery_eur']]})
    visual(b,'Vendors','clusteredBarChart',740,22,518,590,{'Category':[projection('Vendors','vendor_name',active=True)],'Y':[projection('Vendors','gross_loss_eur')]})
    visual(c,'Cases In Queue','cardVisual',22,24,315,142,{'Data':[projection('Audit','Cases In Queue',True)]})
    visual(c,'Audit table','tableEx',22,202,1230,445,{'Values':[projection('Audit',v) for v in ['payment_id','vendor_id','issue_type','priority_score','financial_exposure_eur','status','owner']]})
    (root/'README.md').write_text('''# Power BI Desktop source project (PBIP)\n\nOpen `ProfitLeak_Atlas.pbip` in Power BI Desktop **on Windows**. This is\nsource code (PBIR report + TMDL semantic model) with a *self-contained snapshot*\nof monthly financial metrics, root causes, 40 suppliers and 200 audit queue cases.\nThe full 220k transaction mart remains in the parent repository and should be\nloaded separately if further drill-through is required. No external credentials\nor absolute file path needed for the embedded snapshot.\n\n**Status:** JSON files have been structurally checked, but no Windows Power BI\nDesktop execution is available in the authoring environment. Please open and\nrefresh in Desktop, then save a `.pbix` for deployment. This is NOT a verified\nPBIX or guaranteed deployment-ready report.\n\nMetrics are hypothetical and all data synthetic.\n''',encoding='utf8')
    print('PBIP source created:',root,'tables',n,'pages',len(pages))
    return n
if __name__=='__main__':build()
