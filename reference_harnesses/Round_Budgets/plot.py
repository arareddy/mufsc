#!/usr/bin/env python3
import os
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).resolve().parent/'.mplconfig')
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import json,csv,statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
W=Path(__file__).resolve().parent
assert json.loads((W/'verification.json').read_text())['status']=='PASS'
rows=list(csv.DictReader((W/'tables/key_medians.csv').open()))
for r in rows:
 for k in ['T','seed']:r[k]=int(r[k])
 for k in ['algorithm_seconds','e2e_seconds','Phi']:r[k]=float(r[k])
methods=['fresh','none','basic','runnerup'];names=['Fresh','Direct','Basic','Runner-up']
colors=['#242B35','#0072B2','#D55E00','#009E73'];styles=['-','--',':','-.'];markers=['o','s','D']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'axes.labelsize':11,'axes.titlesize':12})
for ds in ['adult','bank','credit']:
 fig,axs=plt.subplots(1,2,figsize=(12,6),sharey=True)
 for ax,metric,title in zip(axs,['algorithm_seconds','e2e_seconds'],['Algorithm time','End-to-end request time']):
  for m,name,col,ls in zip(methods,names,colors,styles):
   rr=[r for r in rows if r['dataset']==ds and r['method']==m]
   for seed in sorted({r['seed'] for r in rr}):
    s=sorted((r for r in rr if r['seed']==seed),key=lambda x:x['T'])
    ax.plot([r[metric] for r in s],[r['Phi'] for r in s],color=col,alpha=.14,lw=.6,ls=ls)
   xx=[];yy=[]
   for T in range(3):
    s=[r for r in rr if r['T']==T];x=st.mean(r[metric] for r in s);y=st.mean(r['Phi'] for r in s)
    xx.append(x);yy.append(y)
    ax.errorbar(x,y,xerr=st.stdev(r[metric] for r in s),yerr=st.stdev(r['Phi'] for r in s),fmt='none',color=col,alpha=.22,capsize=3,lw=.8)
    ax.plot(x,y,marker=markers[T],markersize=6.5,markerfacecolor='white',markeredgecolor=col,markeredgewidth=1.4,zorder=5)
   ax.plot(xx,yy,color=col,ls=ls,lw=1.7,label=name)
   if m=='fresh':
    for T,(x,y) in enumerate(zip(xx,yy)):ax.annotate(f'C{T}',(x,y),xytext=(7,7),textcoords='offset points',color=col,fontsize=9,fontweight='bold')
  ax.set_title(title,pad=14);ax.set_xlabel('Cumulative time for one request (seconds)');ax.grid(alpha=.15);ax.set_xlim(left=0);ax.margins(y=.18)
 axs[0].set_ylabel('Fairness cost Phi: maximum group-average squared distance')
 fig.suptitle(f'{ds.title()} | fairness versus refinement budget',fontsize=17,fontweight='bold',x=.055,ha='left',y=.975)
 fig.text(.055,.915,'k = 10  |  5 original P2 seeds  |  independent record-deletion batches  |  exact matched-budget replay',fontsize=10,color='#4b5563')
 handles=[Line2D([0],[0],color=c,lw=2,ls=ls,label=n) for n,c,ls in zip(names,colors,styles)]
 fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.89),ncol=4,frameon=False,columnspacing=2.5)
 budget=[Line2D([0],[0],color='#4b5563',marker=markers[t],ls='',markerfacecolor='white',label=f'C{t}: {t} refinement round'+('s' if t!=1 else '')) for t in range(3)]
 fig.legend(handles=budget,loc='lower center',bbox_to_anchor=(.5,.095),ncol=3,frameon=False)
 fig.text(.055,.070,'Markers: mean across seeds of each key\'s four-repeat median time; bars: +/-1 seed SD. Faint lines: individual seeds.',fontsize=9,color='#4b5563')
 fig.text(.055,.041,'All methods have identical quality at each matched seed/budget. C0 still communicates summaries; network time is unmeasured.',fontsize=9,color='#4b5563')
 fig.text(.055,.013,'Budgets are independently rerun cumulative calls, not a Pareto-frontier proof or a sequence of deletion requests.',fontsize=9,color='#4b5563')
 fig.subplots_adjust(left=.075,right=.98,bottom=.23,top=.78,wspace=.17)
 fig.savefig(W/'figures'/f'{ds}_round_budgets.pdf',metadata={'Title':f'{ds.title()}: fairness versus refinement budget','Author':'Fair to Forget bounded experiment','CreationDate':None,'ModDate':None})
 plt.close(fig)
print('Generated 3 figure PDFs')
