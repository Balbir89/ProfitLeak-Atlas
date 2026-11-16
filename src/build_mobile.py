"""Render a static, iPhone Files / Quick Look-safe standalone financial dashboard.

Intentionally does not ship JavaScript: all KPIs, SVG charts, tables and scenarios
are pre-rendered from the synthetic marts. An optional printable PDF can be
made from the generated HTML with a PDF-capable browser.
"""
from pathlib import Path
import csv
import html
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'dashboard'/'ProfitLeak_Atlas_iPhone.html'

def read(name):
    with (ROOT/'data'/'marts'/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

m = json.loads((ROOT/'data'/'marts'/'metrics.json').read_text())
monthly = read('monthly.csv')
causes = read('root_causes.csv')
vendors = read('vendors.csv')
cases = read('sample_for_excel.csv')

def eur(x): return '€' + f'{float(x):,.0f}'
def big(x):
    x=float(x)
    if x>=1_000_000: return '€'+f'{x/1_000_000:,.2f}'+'M'
    if x>=1_000: return '€'+f'{x/1000:,.1f}'+'K'
    return eur(x)
def txt(x): return html.escape(str(x),quote=True)
def num(x):return f'{int(x):,}'

def linechart():
    W,H=720,240
    left,right,top,bottom=69,14,20,43
    wide=W-left-right; height=H-top-bottom
    mx=max(float(x['gross_loss_eur']) for x in monthly)*1.12
    def x(i):return left+i*wide/(len(monthly)-1)
    def y(v):return top+height*(1-float(v)/mx)
    svg=[f'<svg class="trend-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Monthly gross leakage and modeled recovery, 2025 to 2026">']
    for fraction in (0,.25,.5,.75,1):
        yy=y(mx*fraction)
        svg.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{W-right}" y2="{yy:.1f}" stroke="#35465c" stroke-dasharray="5 5"/>')
        svg.append(f'<text x="{left-10}" y="{yy+4:.1f}" text-anchor="end" font-size="11" fill="#9bb0c5">{big(mx*fraction)}</text>')
    for col,name in (('#4de1bd','gross_loss_eur'),('#929bff','modeled_recovery_eur')):
        pts=' '.join(f'{x(i):.1f},{y(row[name]):.1f}' for i,row in enumerate(monthly))
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
    for i in (0,4,8,12,16,20,len(monthly)-1):
        mm=monthly[i]['payment_month']
        label=mm[2:].replace('-','/')
        svg.append(f'<text x="{x(i):.1f}" y="{H-11}" text-anchor="middle" fill="#a8bdd2" font-size="12">{label}</text>')
    svg.append('</svg>')
    return ''.join(svg)

maxloss=max(float(x['gross_loss_eur']) for x in causes)
causecards=[]
for c in causes:
    amount=float(c['gross_loss_eur'])
    fraction=100*amount/maxloss if maxloss else 0
    cue='Control risk only' if amount==0 else f'{num(c["flagged_payments"])} flags'
    causecards.append(f'''<div class="cause-row"><div class="cause-top"><span>{txt(c['issue_type'])}</span><strong>{big(amount) if amount else '€0'}</strong></div>
      <div class="bar"><div class="barfill" style="width:{fraction:.2f}%"></div></div><div class="causenote">{cue}</div></div>''')

vendorrows=[]
for i, v in enumerate(vendors[:8]):
    vendorrows.append(f'''<article class="vendor"><div class="vendor-rank">{i+1:02d}</div><div class="vendor-info"><div class="vendor-name">{txt(v['vendor_name'])}</div><div class="vendor-sub">{txt(v['country'])} · {txt(v['category'])} · {num(v['payments'])} payments</div><div class="vendor-recovery">Modeled recovery: {eur(v['modeled_recovery_eur'])}</div></div><div class="vendor-loss">{eur(v['gross_loss_eur'])}</div></article>''')

casecards=[]
for i, c in enumerate(cases[:8]):
    casecards.append(f'''<article class="case"><div class="casehead"><span class="case-id">{txt(c['payment_id'])}</span><span class="case-value">{eur(c['estimated_gross_loss_eur'])}</span></div><div class="case-vendor">{txt(c['vendor_name'])}</div><div class="caseissue">{txt(c['issue_type'])}</div><div class="caseaction">{txt(c['recommended_action'])}</div></article>''')

scenarios=[]
recovery=float(m['modeled_recoverable_eur'])
for percent in (25,50,75,100):
    scenarios.append(f'<div class="scenario"><div class="scenario-pct">{percent}% realized</div><strong>{big(recovery*percent/100)}</strong><div class="bar"><div class="barfill" style="width:{percent}%"></div></div></div>')

rate = float(m['gross_estimated_loss_eur']) / float(m['spend_eur']) * 100
flags_rate = float(m['flagged_payments'])/float(m['payments'])*100
control=next((num(c['flagged_payments']) for c in causes if c['issue_type']=='Approval fragmentation'),'0')

page = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<meta name="color-scheme" content="dark"><title>ProfitLeak Atlas — iPhone Executive Dashboard</title>
<style>
:root{--bg:#0a1220;--panel:#14243a;--panel2:#192b42;--stroke:#30445c;--txt:#f3f8ff;--muted:#a0b2c8;--mint:#50e0b5;--blue:#929bff;--gold:#ffc47b;--coral:#ff7990}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;padding:0;background:linear-gradient(150deg,#091322 0%,#0e1b2f 60%,#0a1525 100%);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;line-height:1.45;overflow-wrap:break-word}main{max-width:1120px;margin:auto;padding:22px 22px 70px}h1,h2,p{margin:0}h2{font-size:18px;letter-spacing:-.2px}small{color:var(--muted)}.topbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding-bottom:17px;border-bottom:1px solid var(--stroke)}.brand{font-size:16px;font-weight:850;letter-spacing:1.7px}.brand b{color:var(--mint)}.badge{color:var(--mint);font-weight:750;letter-spacing:1px;border:1px solid #50e0b54c;border-radius:20px;padding:6px 11px;font-size:10px}.eyebrow{color:var(--mint);font-weight:800;letter-spacing:2.1px;font-size:10px;margin-bottom:8px}.hero{margin:26px 0 20px;display:grid;grid-template-columns:1.2fr .8fr;gap:15px;align-items:stretch}.hero h1{font-size:clamp(29px,4.4vw,52px);line-height:1.1;letter-spacing:-.9px;margin-bottom:10px}.hero h1 span{color:var(--mint)}.hero p{font-size:13px;color:var(--muted);max-width:600px}.recovery{padding:17px 18px;border:1px solid #50e0b55c;border-radius:18px;background:linear-gradient(145deg,#10433744,#152740);display:flex;flex-direction:column;justify-content:center}.recovery label{color:var(--mint);letter-spacing:1px;font-weight:800;font-size:10px}.recovery strong{font-size:clamp(30px,4vw,43px);line-height:1.2;margin:9px 0}.recovery small{font-size:11px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin:20px 0}.kpi{min-width:0;background:var(--panel);border:1px solid var(--stroke);border-radius:14px;padding:16px 13px;box-shadow:0 1px 0 #ffffff0a inset}.kpi:before{content:'';display:block;height:3px;width:29px;background:var(--mint);margin-bottom:14px}.kpi:nth-child(2):before{background:var(--gold)}.kpi:nth-child(3):before{background:var(--blue)}.kpi:nth-child(4):before{background:var(--coral)}.kpi-label{font-size:10px;text-transform:uppercase;color:#b5c5d7;letter-spacing:1px;font-weight:750;line-height:1.5}.kpi-value{font-size:clamp(23px,3vw,32px);font-weight:850;letter-spacing:-.6px;margin:9px 0}.kpi-note{font-size:10px;color:var(--muted)}.cols{display:grid;grid-template-columns:1.12fr .88fr;gap:13px;margin:13px 0}.card{min-width:0;background:var(--panel);border:1px solid var(--stroke);border-radius:18px;padding:19px}.card-head{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:15px}.card-head small{font-size:11px;display:block;margin-top:5px}.chip{font-size:10px;letter-spacing:.7px;color:#bdcde0;border:1px solid #52617b;border-radius:24px;padding:6px 9px;white-space:nowrap}.trend-svg{display:block;width:100%;height:auto;max-height:245px}.legend{display:flex;gap:18px;flex-wrap:wrap;color:#b6c6d9;font-size:11px;margin:8px 0 0}.legend i{width:9px;height:9px;display:inline-block;background:var(--mint);border-radius:50%;margin-right:5px}.legend .blue{background:var(--blue)}.cause-row{margin:14px 0 18px}.cause-top{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:12px}.cause-top strong{font-size:13px;white-space:nowrap}.bar{height:9px;background:#27384e;border-radius:12px;overflow:hidden;margin:7px 0 4px}.barfill{height:100%;background:linear-gradient(90deg,#36b999,var(--mint));border-radius:12px}.causenote{font-size:10px;color:var(--muted)}.fine{color:var(--muted);font-size:11px;line-height:1.7}.scenarios{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:17px}.scenario{padding:12px;background:#102038;border:1px solid #2c4059;border-radius:12px}.scenario-pct{color:var(--muted);font-size:11px}.scenario strong{display:block;font-size:19px;margin-top:6px;color:var(--mint)}.note{margin-top:12px;border:1px solid #30546d;background:#12273b;padding:13px;border-radius:12px;font-size:12px;color:#c5d7e8}.wide{margin-top:13px}.vendors{display:grid;grid-template-columns:1fr 1fr;gap:9px}.vendor{min-width:0;display:flex;align-items:flex-start;gap:10px;background:#102138;border:1px solid #29425d;padding:11px;border-radius:12px}.vendor-rank{font-size:11px;color:var(--mint);font-weight:900}.vendor-info{flex:1;min-width:0}.vendor-name{font-weight:750;font-size:12px}.vendor-sub,.vendor-recovery{font-size:10px;color:var(--muted);margin-top:5px}.vendor-loss{font-weight:850;color:var(--gold);font-size:12px;white-space:nowrap}.casegrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.case{background:#102138;border:1px solid #29425d;border-radius:12px;padding:13px}.casehead{display:flex;justify-content:space-between;gap:5px;align-items:center}.case-id{color:var(--muted);font-size:10px;font-weight:750}.case-value{color:var(--gold);font-size:14px;font-weight:850}.case-vendor{font-size:11px;font-weight:750;margin:9px 0 6px}.caseissue{display:inline-block;border-radius:7px;padding:4px 7px;color:#ffe1b1;background:#4b342a;font-size:9px}.caseaction{color:#a5bbd3;font-size:10px;line-height:1.4;margin-top:9px}.foot{padding-top:17px;border-top:1px solid var(--stroke);color:var(--muted);font-size:11px;margin-top:27px;line-height:1.6}.foot strong{color:#d7e7f6}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:16px}.fact{background:#102138;border-radius:12px;border:1px solid #28425b;padding:12px}.fact-label{font-size:10px;color:var(--muted)}.fact strong{display:block;font-size:18px;margin-top:7px}
@media(max-width:900px){.hero{grid-template-columns:1fr 1fr}.kpis{grid-template-columns:repeat(2,1fr)}.cols{grid-template-columns:1fr}.casegrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:520px){main{padding:17px 14px 44px}.brand{font-size:14px}.hero{display:flex;flex-direction:column;margin-top:23px}.hero h1{font-size:34px}.recovery{padding:14px}.recovery strong{font-size:34px}.kpis{gap:8px}.kpi{padding:12px 11px}.kpi-label{font-size:9px;letter-spacing:.6px}.kpi-value{font-size:24px}.kpi-note{font-size:9px}.card{padding:15px}.card-head h2{font-size:17px}.chip{font-size:9px}.scenarios{grid-template-columns:repeat(2,1fr)}.vendors{grid-template-columns:1fr}.casegrid{grid-template-columns:1fr 1fr;gap:7px}.case{padding:10px}.casehead{flex-wrap:wrap}.facts{grid-template-columns:1fr 1fr}.trend-svg{width:100%}}
@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}body{background:#fff;color:#101b2a}main{padding:7mm;max-width:100%}.hero,.cols,.kpis,.vendors,.casegrid{break-inside:avoid}.card,.kpi,.vendor,.case{break-inside:avoid}a{color:inherit}.foot{page-break-inside:avoid}@page{size:A4;margin:7mm}}
</style></head><body><main>
<header class="topbar"><div class="brand">◈ PROFITLEAK <b>ATLAS</b></div><div class="badge">● SYNTHETIC DEMO</div></header>
<div class="hero"><section><div class="eyebrow">FINANCIAL FORENSICS / MOBILE EDITION</div><h1>Find the losses.<br><span>Prove the story.</span></h1><p>Offline executive overview of synthetic corporate procurement exception detection. All figures are embedded directly into this document, without JavaScript.</p></section><div class="recovery"><label>MODELED RECOVERABLE VALUE</label><strong>__RECOVERY__</strong><small>Potential exposure, not actual recovered cash</small></div></div>
<div class="kpis">
<div class="kpi"><div class="kpi-label">Total payment spend</div><div class="kpi-value">__SPEND__</div><div class="kpi-note">220,000 payments · EUR</div></div>
<div class="kpi"><div class="kpi-label">Gross leakage exposure</div><div class="kpi-value">__LOSS__</div><div class="kpi-note">Estimated · unconfirmed</div></div>
<div class="kpi"><div class="kpi-label">Flagged payments</div><div class="kpi-value">__FLAGS__</div><div class="kpi-note">__FLAGS_RATE__% of all payments</div></div>
<div class="kpi"><div class="kpi-label">Gross leakage rate</div><div class="kpi-value">__RATE__%</div><div class="kpi-note">Estimated loss ÷ spend</div></div>
</div>
<div class="cols"><section class="card"><header class="card-head"><div><h2>Leakage velocity</h2><small>Gross exposure vs modeled recovery by month</small></div><span class="chip">22 MONTHS</span></header>__CHART__<div class="legend"><span><i></i> Gross exposure</span><span><i class="blue"></i> Modeled recovery</span></div></section>
<section class="card"><header class="card-head"><div><h2>Where exposure originates</h2><small>Estimated impact by root cause</small></div><span class="chip">6 RULES</span></header>__CAUSES__<p class="fine">Approval fragmentation is a process risk, not a cash loss.</p></section></div>
<section class="card wide"><header class="card-head"><div><h2>Recovery scenarios</h2><small>What if some proportion of modeled recovery is realized?</small></div><span class="chip">ILLUSTRATIVE</span></header><p class="fine">Scenario sensitivity is not a prediction or a claim of recovered funds.</p><div class="scenarios">__SCENARIOS__</div></section>
<div class="facts"><div class="fact"><div class="fact-label">Pure control-risk flags</div><strong>__CONTROL__</strong></div><div class="fact"><div class="fact-label">Verified fraud</div><strong>0</strong></div><div class="fact"><div class="fact-label">Confirmed vendor credits</div><strong>€0</strong></div></div>
<section class="card wide"><header class="card-head"><div><h2>Highest-exposure vendors</h2><small>Top 8 by modeled gross leakage</small></div><span class="chip">PRIORITIES</span></header><div class="vendors">__VENDORS__</div></section>
<section class="card wide"><header class="card-head"><div><h2>Evidence-led casebook</h2><small>Top 8 of the export's highest exposure cases</small></div><span class="chip">CASE SAMPLE</span></header><div class="casegrid">__CASES__</div><p class="fine" style="margin-top:12px">Investigators must reconcile each case with contracts, ledgers, bank statements and vendor records before calling it a confirmed loss.</p></section>
<footer class="foot"><strong>Data origin:</strong> ProfitLeak Atlas project synthetic SQL/Python marts (2025–2026). Values are illustrative, not company results. This edition contains no scripts or external links, so it can be previewed offline on iPhone using Files / Quick Look. <strong>All amounts in EUR.</strong></footer>
</main></body></html>'''

rep={
'__RECOVERY__':big(recovery), '__SPEND__':big(m['spend_eur']),
'__LOSS__':big(m['gross_estimated_loss_eur']), '__FLAGS__':num(m['flagged_payments']),
'__FLAGS_RATE__':f'{flags_rate:.1f}', '__RATE__':f'{rate:.2f}',
'__CHART__':linechart(), '__CAUSES__':''.join(causecards), '__SCENARIOS__':''.join(scenarios),
'__CONTROL__':control, '__VENDORS__':''.join(vendorrows), '__CASES__':''.join(casecards)}
for tag,val in rep.items():
    assert tag in page,tag
    page=page.replace(tag,val)
assert '<script' not in page.lower()
DEST.write_text(page,encoding='utf-8')
print(f'Built {DEST} ({DEST.stat().st_size:,} bytes) | KPIs: {big(m["spend_eur"])}, {big(m["gross_estimated_loss_eur"])}, {num(m["flagged_payments"])}, {rate:.2f}%')
