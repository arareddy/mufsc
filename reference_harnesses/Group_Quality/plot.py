"""Plot verified saved quality; vector PDFs. Run through with_lock.py."""
import os,csv,json,hashlib,subprocess,datetime
from pathlib import Path
from fractions import Fraction
W=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(W/'.mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
rows=list(csv.DictReader((W/'tables/case_quality.csv').open()));summary=list(csv.DictReader((W/'tables/summary.csv').open()))
assert json.loads((W/'VERIFICATION.json').read_text())['status']=='PASS'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
colors={'Phi_A':'#D16B14','Phi_B':'#2473AF','Phi':'#693E8A','population_average':'#178477'}
markers={'Phi_A':'o','Phi_B':'s','Phi':'D','population_average':'v'}
labels={'Phi_A':'Group 0','Phi_B':'Group 1','Phi':'Worst-group cost','population_average':'Population-average cost'}
groupdefs={'adult':'0: not male mask  |  1: male mask','bank':'0: not married  |  1: married','credit':'0: other codes  |  1: education {1, 2}'}
figdir=W/'figures';figdir.mkdir(exist_ok=True);tmp=W/'tmp/pdfs';tmp.mkdir(parents=True,exist_ok=True)
receipts=[]
for pop,title in [('record','A. Record-deletion survivors'),('client','B. Whole-client-deletion survivors')]:
 fig,axs=plt.subplots(2,3,figsize=(12.2,7.15));fig.subplots_adjust(left=.075,right=.98,top=.78,bottom=.23,wspace=.27,hspace=.28)
 fig.suptitle(title+' | group quality across refinement rounds',x=.075,y=.965,ha='left',fontsize=15,fontweight='bold')
 subtitle='Adult / Bank / Credit: 30 / 45 / 30 records removed per seed' if pop=='record' else 'One fixed client removed per dataset: 300 / 2,259 / 299 records'
 fig.text(.075,.92,subtitle+'; k = 10; five seeds (10000-10004).',fontsize=10,color='#444444')
 handles=[Line2D([0],[0],color=colors[k],marker=markers[k],linewidth=2,label=labels[k]) for k in colors]
 fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.067,.89),ncol=4,frameon=False,fontsize=9.5,columnspacing=2.2)
 for col,ds in enumerate(['adult','bank','credit']):
  dsrows=[r for r in rows if r['population']==pop and r['dataset']==ds]
  vals=[float(Fraction(r[k+'_exact'])) for r in dsrows for k in colors];lo,hi=min(vals),max(vals);pad=(hi-lo)*.12
  for row,metrics in enumerate([['Phi_A','Phi_B'],['Phi','population_average']]):
   ax=axs[row,col]
   for k in metrics:
    for seed in range(10000,10005):
     rr=sorted([r for r in dsrows if int(r['seed'])==seed],key=lambda x:int(x['T']))
     ax.plot([0,1,2],[float(Fraction(r[k+'_exact'])) for r in rr],color=colors[k],alpha=.27,linewidth=.8,marker=markers[k],markersize=3,zorder=1)
    ss=sorted([r for r in summary if r['population']==pop and r['dataset']==ds and r['metric']==k],key=lambda x:int(x['T']))
    yy=[float(Fraction(r['mean_exact'])) for r in ss];sd=[float(r['sample_sd']) for r in ss]
    ax.errorbar([0,1,2],yy,yerr=sd,color=colors[k],marker=markers[k],linewidth=2.1,markersize=6,capsize=3,elinewidth=1.15,zorder=3)
   ax.set_ylim(lo-pad,hi+pad);ax.set_xlim(-.12,2.12);ax.set_xticks([0,1,2]);ax.grid(axis='y',color='#dddddd',linewidth=.65);ax.set_axisbelow(True)
   if col==0:ax.set_ylabel('Group-average squared cost' if row==0 else 'Squared cost per record')
   if row==0:ax.set_title(ds.title()+'\n'+groupdefs[ds],pad=9,fontweight='normal')
   else:ax.set_xlabel('T: refinement rounds')
 fig.text(.075,.157,'Thin paths: all five paired seeds. Bold markers: mean across seeds. Bars: +/- one sample SD (n - 1).',fontsize=9)
 fig.text(.075,.124,'Worst-group curve = mean of each seed\'s maximum group cost; population curve = mean of each seed\'s count-weighted cost.',fontsize=8.7)
 fig.text(.075,.091,'Axes show absolute cost with nonzero origins; dataset scales differ. Group masks are frozen; Adult/Credit raw provenance is incomplete.',fontsize=8.5,color='#444444')
 n=3 if pop=='record' else 2
 fig.text(.075,.053,f'Adult, T=1 to T=2: group 1 cost rises in {n}/5 seeds while worst-group cost falls. No ordinary-Lloyd baseline is shown.',fontsize=9,color='#7A3B13')
 path=figdir/f'{pop}_group_quality.pdf';fig.savefig(path,metadata={'Title':title+' group quality','Author':'Fair to Forget saved-evidence analysis','CreationDate':datetime.datetime(2026,9,26,tzinfo=datetime.timezone.utc),'ModDate':datetime.datetime(2026,9,26,tzinfo=datetime.timezone.utc)})
 plt.close(fig)
 # One-page local-only render for required visual QA.
 cmd=['[private-path-omitted]','-r','115','-singlefile','-png',str(path),str(tmp/f'{pop}_group_quality')]
 subprocess.run(cmd,check=True)
 receipts.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,population=pop,seed_paths_per_metric_dataset=5,pdf_pages=1,render=str(tmp/f'{pop}_group_quality.png')))
(W/'FIGURE_RECEIPTS.json').write_text(json.dumps(dict(status='RENDERED_AWAITING_VISUAL_QA',matplotlib_version=matplotlib.__version__,plot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_csv_sha256=hashlib.sha256((W/'tables/case_quality.csv').read_bytes()).hexdigest(),figures=receipts),indent=2)+'\n')
print(json.dumps(receipts,indent=2))
