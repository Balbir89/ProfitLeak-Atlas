"""Offline PBIP/PBIR + TMDL SOURCE checker (NOT Power BI Desktop execution)."""
from __future__ import annotations
import csv, json, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'powerbi/ProfitLeak_Atlas_PBIP'
REPORT=BASE/'ProfitLeak_Atlas.Report'
MODEL=BASE/'ProfitLeak_Atlas.SemanticModel'

def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def checks():
    errors=[];checks=[]
    def require(condition,code):
        checks.append(code)
        if not condition:errors.append(code)
    pbip=read_json(BASE/'ProfitLeak_Atlas.pbip')
    require(pbip.get('version')=='1.0','pbip_version_supported')
    require(pbip['artifacts'][0]['report']['path']==REPORT.name,'pbip_report_folder_reference')
    definition=read_json(REPORT/'definition.pbir')
    linked=(REPORT/definition['datasetReference']['byPath']['path']).resolve()
    require(linked==MODEL.resolve(),'report_links_local_semantic_model')
    require((MODEL/'definition/model.tmdl').exists(),'semantic_model_tmdl_exists')
    tables={}
    for file in (MODEL/'definition/tables').glob('*.tmdl'):
        s=file.read_text(encoding='utf-8');columns=set(re.findall(r'^\s*column\s+(\w+)\s*$',s,re.M))
        measures=set(re.findall(r"^\s*measure\s+'([^']+)'\s*=",s,re.M))
        tables[file.stem]={'columns':columns,'measures':measures}
        require(s.lstrip().startswith('table '+file.stem),'table_object_'+file.stem)
        require('partition '+file.stem+' = m' in s,'import_partition_'+file.stem)
    model_tmdl=(MODEL/'definition/model.tmdl').read_text()
    for table in tables:
        require('ref table '+table in model_tmdl,'tmdl_table_ref_'+table)
    page_order=read_json(REPORT/'definition/pages/pages.json')['pageOrder']
    require(len(page_order)==3,'three_pages')
    page_count=0;visual_count=0;types=Counter()
    for page in page_order:
        p=REPORT/'definition/pages'/page
        require((p/'page.json').exists(),'page_exists_'+page)
        pageinfo=read_json(p/'page.json');page_count+=1
        require(pageinfo['name']==page,'page_id_matches_'+page)
        for visual_path in sorted((p/'visuals').glob('*/visual.json')):
            v=read_json(visual_path);visual_count+=1
            require(v['name']==visual_path.parent.name,'visual_id_'+visual_path.parent.name)
            vdata=v.get('visual',{});typ=vdata.get('visualType');types[typ]+=1
            require(typ in {'cardVisual','lineChart','clusteredBarChart','tableEx'},'visual_type_'+str(visual_count))
            roles=vdata.get('query',{}).get('queryState',{})
            if typ=='cardVisual':require('Data' in roles,'card_role_'+str(visual_count))
            for role,state in roles.items():
                for projection in state.get('projections',[]):
                    field=projection['field'];kind,obj=next(iter(field.items()))
                    table=obj['Expression']['SourceRef']['Entity'];column=obj['Property']
                    require(table in tables and column in tables[table]['measures' if kind=='Measure' else 'columns'],
                            'field_binding_'+table+'_'+column)
            position=v['position']
            require(0<=position['x'] and 0<=position['y'] and position['x']+position['width']<=1280 and position['y']+position['height']<=720,
                    'visual_inside_canvas_'+str(visual_count))
    require(visual_count>=10,'at_least_ten_visuals')
    with (ROOT/'data/marts/monthly.csv').open(newline='',encoding='utf-8') as monthly_file:
        monthly_rows=list(csv.DictReader(monthly_file))
    metrics=read_json(ROOT/'data/marts/metrics.json')
    import decimal
    total=lambda col:sum((decimal.Decimal(r[col]) for r in monthly_rows),decimal.Decimal('0'))
    require(abs(total('spend_eur')-decimal.Decimal(str(metrics['spend_eur'])))<decimal.Decimal('.10'),'monthly_spend_reconciles')
    require(abs(total('gross_loss_eur')-decimal.Decimal(str(metrics['gross_estimated_loss_eur'])))<decimal.Decimal('.10'),'monthly_exposure_reconciles')
    require(sum(int(r['payments']) for r in monthly_rows)==metrics['payments'],'monthly_payment_count_reconciles')
    result={'kind':'offline_source_structural_consistency','pbip_files_examined':len(list(BASE.rglob('*'))),
           'tables':len(tables),'pages':page_count,'visuals':visual_count,'visual_types':dict(types),
           'checks_executed':len(checks),'checks_failed':errors,'offline_source_checks_passed':len(errors)==0,
           'power_bi_desktop_runtime_executed':False,'power_bi_desktop_visuals_verified':False,
           'actual_pbix_created':False,
           'limitation':'Successful JSON/TMDL source checks do not prove the project can load, refresh, or render in Windows Power BI Desktop.'}
    (ROOT/'docs/powerbi_source_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit('PBIP SOURCE VALIDATION FAILED: '+','.join(errors))
    return result
if __name__=='__main__': checks()
