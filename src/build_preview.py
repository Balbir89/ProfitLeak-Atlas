"""Generate a crisp README marketing preview based on actual synthetic metrics."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patheffects
ROOT=Path(__file__).resolve().parents[1]
metrics=json.loads((ROOT/'data/marts/metrics.json').read_text())
def csvrows(n):
 with (ROOT/'data/marts'/n).open() as f:return list(csv.DictReader(f))
months=csvrows('monthly.csv');causes=csvrows('root_causes.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig=plt.figure(figsize=(15.2,8.6),dpi=155,facecolor='#0B1220')
fig.text(.048,.94,'◈  PROFITLEAK ATLAS',fontsize=27,fontweight='bold',color='#F4F8FE')
fig.text(.051,.895,'FINANCIAL FORENSICS  /  EXECUTIVE INTELLIGENCE  /  100% SYNTHETIC',fontsize=10,color='#4FE0B5',fontweight='bold')
fig.text(.951,.945,'EU PROCUREMENT  •  2025–2026',fontsize=10,color='#A6B8CF',ha='right')
fig.text(.05,.835,'Simulated procurement exposure and recovery scenarios',fontsize=15,color='#CBD8E8')
blocks=[('PAYMENT SPEND',metrics['spend_eur'],'#4FE0B5'),('GROSS EXPOSURE',metrics['gross_estimated_loss_eur'],'#FFBB78'),('MODELED RECOVERY',metrics['modeled_recoverable_eur'],'#899BFF'),('FLAGGED TRANSACTIONS',metrics['flagged_payments'],'#FF7384')]
for i,(title,value,color) in enumerate(blocks):
 x=.051+.237*i
 from matplotlib.patches import FancyBboxPatch
 fig.patches.append(FancyBboxPatch((x,.635),.216,.16,boxstyle='round,pad=0.013',transform=fig.transFigure,facecolor='#17273B',edgecolor='#30445B',lw=1))
 fig.text(x+.014,.754,title,color='#9DB1C8',fontsize=10,fontweight='bold')
 label=f'€{value/1e6:,.2f}M' if title!='FLAGGED TRANSACTIONS' else f'{value:,}'
 fig.text(x+.014,.685,label,color='#F6F9FC',fontsize=27,fontweight='bold')
 fig.patches.append(FancyBboxPatch((x+.014,.788),.047,.003,boxstyle='square,pad=0',transform=fig.transFigure,facecolor=color,edgecolor='none'))
ax=fig.add_axes([.065,.158,.52,.40],facecolor='#17273B')
y=[float(m['gross_loss_eur'])/1e6 for m in months];y2=[float(m['modeled_recovery_eur'])/1e6 for m in months]
x=list(range(len(y)));ax.plot(x,y,color='#4FE0B5',lw=2.6,label='Gross leakage');ax.fill_between(x,y,color='#4FE0B5',alpha=.10)
ax.plot(x,y2,color='#899BFF',ls='--',lw=2.1,label='Modeled recovery')
ax.set_title('LEAKAGE VELOCITY  |  MONTHLY EXPOSURE',loc='left',color='white',fontweight='bold',pad=20,fontsize=12)
ax.set_xticks([0,4,8,12,16,21], [months[k]['payment_month'][2:] for k in [0,4,8,12,16,21]])
ax.set_ylabel('EUR (millions)',color='#A8BDD2');ax.tick_params(colors='#AFBFD0')
ax.grid(alpha=.2,color='#A3B5CA',linestyle=':');ax.legend(loc='upper left',frameon=False,labelcolor='#D6E3EE')
for s in ax.spines.values():s.set_visible(False)
ax2=fig.add_axes([.715,.158,.245,.40],facecolor='#17273B')
c=[x for x in causes if float(x['gross_loss_eur'])>0];c=list(reversed(c))
labels=[x['issue_type'].replace('Contract price variance','Contract pricing').replace('Missed early discount','Missed discount').replace('Undelivered goods','Receipt gaps').replace('Duplicate payment','Duplicate payments').replace('FX spread excess','FX spread') for x in c]
ax2.barh(range(len(c)),[float(x['gross_loss_eur'])/1e6 for x in c],color='#4FE0B5',height=.55)
ax2.set_yticks(range(len(c)),labels,color='#CCD9E6',fontsize=9)
ax2.tick_params(axis='y',length=0);ax2.set_xlim(0,6.2);ax2.set_xticks([0,2,4,6],['€0M','€2M','€4M','€6M'],color='#A8BDD2')
ax2.set_title('LOSS DRIVERS',loc='left',color='white',fontweight='bold',pad=20,fontsize=12)
ax2.grid(axis='x',alpha=.2,linestyle=':');ax2.set_axisbelow(True)
for s in ax2.spines.values():s.set_visible(False)
fig.text(.05,.065,'SQL DETECTION   •   EXCEL AUDIT MODEL   •   PYTHON PIPELINE   •   POWER BI SOURCE   •   INTERACTIVE HTML',fontsize=10,color='#9AB0C9',fontweight='bold')
fig.text(.05,.033,'Illustrative portfolio case study. No real transactions, fraud claims or recovered money.',fontsize=9,color='#8A9FB4')
out=ROOT/'docs/images/executive_dashboard_preview.png'
fig.savefig(out,facecolor=fig.get_facecolor(),bbox_inches='tight',pad_inches=.16)
plt.close(fig)
print('Preview:',out)
