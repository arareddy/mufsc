"""Compact scientific appendix artifact from saved, verified tables."""
from pathlib import Path
import os,csv,statistics,json
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'scratch/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
read=lambda f:list(csv.DictReader((ROOT/'tables'/f).open()))
a=read('aggregate_timings.csv');q=read('quality_exact.csv')
assert len(q)==45
plt.rcParams.update({'font.size':8.5,'axes.titlesize':10,'axes.labelsize':8.5,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(2,3,figsize=(9.2,5.7),gridspec_kw={'height_ratios':[1,1]})
colors={'direct':'#1763a6','basic':'#bb681c','runnerup':'#388469'}
markers={'direct':'o','basic':'s','runnerup':'^'}
for j,ds in enumerate(('adult','bank','credit')):
 ax=axes[0,j]
 for offset,m in zip((-.06,0,.06),('direct','basic','runnerup')):
  rows=[next(r for r in a if r['dataset']==ds and r['T']==str(T) and r['method']==m and r['scope']=='request') for T in (1,2)]
  y=[float(r['ratio_of_total_times']) for r in rows]
  lo=[v-float(r['paired_min']) for v,r in zip(y,rows)];hi=[float(r['paired_max'])-v for v,r in zip(y,rows)]
  ax.errorbar([1+offset,2+offset],y,yerr=[lo,hi],color=colors[m],marker=markers[m],linewidth=1.6,markersize=4,capsize=2.5,label={'direct':'Direct','basic':'Basic','runnerup':'Runner-up'}[m])
 ax.axhline(1,color='#666666',linewidth=.7,linestyle='--')
 ax.set(xlim=(.72,2.28),ylim=(.95,2.95),xticks=[1,2],title=ds.title(),xlabel='Refinement rounds T')
 ax.grid(axis='y',alpha=.18)
 if j==0:ax.set_ylabel('Fresh / replay request time')
 ax=axes[1,j]
 vals=[];low=[];high=[]
 for T in (0,1,2):
  rows=[r for r in q if r['dataset']==ds and int(r['T'])==T]
  ratios=[100*float(r['Phi'])/float(next(b for b in q if b['parent_case_id']==r['parent_case_id'] and b['T']=='0')['Phi']) for r in rows]
  v=statistics.mean(ratios);vals.append(v);low.append(v-min(ratios));high.append(max(ratios)-v)
 ax.errorbar([0,1,2],vals,yerr=[low,high],color='#74439b',marker='D',markersize=4,linewidth=1.6,capsize=3)
 ax.set(xlim=(-.2,2.28),ylim=(56,110),xticks=[0,1,2],xlabel='Refinement rounds T')
 ax.grid(axis='y',alpha=.18)
 if j==0:ax.set_ylabel('Worst-group cost (% of T=0)')
 for x,y,upper in zip((0,1,2),vals,high):ax.annotate(f'{y:.1f}%',(x,y+upper),xytext=(0,7),textcoords='offset points',ha='center',fontsize=7.5)
fig.suptitle('Whole-client deletion: speedup survives one and two fair-refinement rounds',fontsize=11.5,y=.98)
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.935),ncol=3,frameon=False)
fig.subplots_adjust(left=.085,right=.985,bottom=.21,top=.84,hspace=.45,wspace=.26)
caption=('Top: matched-budget canonical FTF-1D; ratio of total resident-request times, four repetitions per setting.\n'
         'Bars span five paired seed ratios (not confidence intervals). Bottom: mean paired Phi(T)/Phi(0); bars span five seeds.\n'
         'Phi = max(group-average costs). Quality reuses exact same-population witnesses, matched to every new fresh output.\n'
         'k=10; seeds 10000-10004; one fixed whole-client request per dataset. Initialization already communicates at T=0.\n'
         'No compact-fast method is measured at T=1/2; historical T=0 performance is not plotted. Run: client-refinement-20260926-v1.')
fig.text(.085,.025,caption,ha='left',va='bottom',fontsize=7.1,linespacing=1.45)
(ROOT/'output').mkdir(exist_ok=True);(ROOT/'scratch').mkdir(exist_ok=True)
fig.savefig(ROOT/'output/whole_client_refinement_appendix.pdf',metadata={'Title':'Whole-client deletion with fair refinement','Subject':'Matched-budget canonical replay and verified same-population quality; 30 settings, 480 timing observations'})
fig.savefig(ROOT/'scratch/appendix_preview.png',dpi=180)
print('Created one-page appendix PDF and local QA preview.')
