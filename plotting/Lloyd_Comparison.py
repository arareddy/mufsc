from pathlib import Path
import os,json,hashlib
W=Path(os.environ['FTF_PLOT_OUTPUT'])
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
import csv,datetime,subprocess
os.environ['MPLCONFIGDIR']=str(W/'.mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
assert load(W/'VERIFICATION.json')['status']=='PASS'
rows=list(csv.DictReader((W/'tables/paired_methods.csv').open()));summ=list(csv.DictReader((W/'tables/paired_methods_summary.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
colors=dict(Phi_A='#D16B14',Phi_B='#2473AF',Phi='#693E8A',population_average='#178477');marks=dict(Phi_A='o',Phi_B='s',Phi='D',population_average='v');labels=dict(Phi_A='Group 0 cost',Phi_B='Group 1 cost',Phi='Worst-group cost',population_average='Population-average cost')
groups=dict(adult='0: not male mask | 1: male mask',bank='0: not married | 1: married',credit='0: other codes | 1: education {1, 2}')
fig,axes=plt.subplots(2,3,figsize=(12.2,7.2));fig.subplots_adjust(left=.075,right=.975,top=.76,bottom=.25,wspace=.25,hspace=.35)
fig.suptitle('Guarded fair versus ordinary Lloyd updates',x=.075,y=.965,ha='left',fontsize=16,fontweight='bold')
fig.text(.075,.918,'Identical fair-initialized centers and retained records; k = 10; five paired seeds per dataset and population.',fontsize=10,color='#444444')
fig.legend(handles=[Line2D([0],[0],color=colors[k],marker=marks[k],label=labels[k],lw=2) for k in colors],loc='upper left',bbox_to_anchor=(.068,.89),ncol=4,frameon=False,fontsize=9.5)
for i,pop in enumerate(['record','client']):
 for j,ds in enumerate(['adult','bank','credit']):
  ax=axes[i,j];ax.axhline(0,color='#777777',linewidth=.8,linestyle='--')
  for k in colors:
   for seed in range(10000,10005):
    rr=sorted([r for r in rows if (r['population'],r['dataset'],int(r['seed']),r['metric'])==(pop,ds,seed,k)],key=lambda r:int(r['T']))
    ax.plot([0,1,2],[100*float(r['relative_difference']) for r in rr],color=colors[k],alpha=.20,lw=.8,marker=marks[k],ms=2.8,zorder=1)
   ss=sorted([r for r in summ if (r['population'],r['dataset'],r['metric'])==(pop,ds,k)],key=lambda r:int(r['T']))
   ax.errorbar([0,1,2],[100*float(r['relative_difference_mean']) for r in ss],yerr=[100*float(r['relative_difference_sample_sd']) for r in ss],color=colors[k],lw=1.8,marker=marks[k],ms=5,capsize=3,elinewidth=1,zorder=3)
  ax.set_xticks([0,1,2]);ax.set_xlim(-.12,2.12);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
  if i==0:ax.set_title(ds.title()+'\n'+groups[ds],pad=9)
  if j==0:ax.set_ylabel(('Record deletion' if pop=='record' else 'Whole-client deletion')+'\nFair minus Lloyd (%)')
  if i==1:ax.set_xlabel('T: refinement rounds')
fig.text(.075,.155,'Each point uses 100 x (fair cost - Lloyd cost) / Lloyd cost within seed. Negative means lower cost with fair updates.',fontsize=9)
fig.text(.075,.121,'Thin paths: all five seeds. Bold markers: mean paired percentage difference. Bars: one sample SD; dataset scales differ.',fontsize=9)
fig.text(.075,.087,'T0 is the shared initialization. The studies have distinct survivors. Absolute costs, exact fractions and every case are in the tables.',fontsize=8.7,color='#444444')
fig.text(.075,.05,'Fair updates lower worst-group cost here, with higher population-average and group 1 costs. This tests update choice, not initialization.',fontsize=9,color='#673C20')
(W/'figures').mkdir(exist_ok=True);(W/'tmp/pdfs').mkdir(parents=True,exist_ok=True)
p=W/'figures/matched_start_quality.pdf';fig.savefig(p,metadata={'Title':'Matched-start fair versus Lloyd refinement','Author':'Fair to Forget bounded comparison','CreationDate':datetime.datetime(2026,9,26,tzinfo=datetime.timezone.utc),'ModDate':datetime.datetime(2026,9,26,tzinfo=datetime.timezone.utc)});plt.close(fig)
dump(W/'FIGURE_RECEIPT.json',dict(status='RENDERED_AWAITING_VISUAL_QA',path=str(p),sha256=sha(p),bytes=p.stat().st_size,plot_sha256=sha(Path(__file__)),paired_table_sha256=sha(W/'tables/paired_methods.csv'),matplotlib=matplotlib.__version__))
print(p)
