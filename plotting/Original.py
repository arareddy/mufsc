"""Replot original P1/P3/P4 quantities from saved CSVs (portable style)."""
from pathlib import Path
import os,csv
R=Path(__file__).resolve().parents[1];W=Path(os.environ['FTF_PLOT_OUTPUT']);os.environ['MPLCONFIGDIR']=str(W/'.mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
def rows(p):return list(csv.DictReader(p.open()))
def save(fig,name):fig.savefig(W/'figures'/name,bbox_inches='tight',metadata={'Author':None,'CreationDate':None,'ModDate':None});plt.close(fig)
colors={'centralized':'#555555','splitgroup_2k':'#1976b9','merged_1k':'#ce4343','merged_2k':'#d29527'}
p1=rows(R/'evidence/p1_p4/p1_full/p1_summary.csv');fig,ax=plt.subplots(figsize=(7,3.8))
for method,col in colors.items():
 rr=sorted([r for r in p1 if r['method']==method],key=lambda r:int(r['kappa']));ax.errorbar([int(r['kappa']) for r in rr],[float(r['ratio_G']) for r in rr],yerr=[float(r['se_ratio_G']) for r in rr],marker='o',ms=3,color=col,label=method)
ax.set_xscale('log',base=2);ax.set_xlabel('Heterogeneity kappa');ax.set_ylabel('Mean G / G*');ax.set_title('P1: 10,000 seeds per method and kappa');ax.legend(frameon=False,ncol=2);ax.grid(alpha=.2);save(fig,'corrected_p1.pdf')
p4=rows(R/'evidence/p1_p4/p4_settings.csv');fig,axs=plt.subplots(2,3,figsize=(10,5.8),layout='constrained')
for j,ds in enumerate(['adult','bank','credit']):
 for method,col in colors.items():
  rr=[r for r in p4 if r['dataset']==ds and r['method']==method]
  if method=='centralized':axs[0,j].axhline(float(rr[0]['final_Phi']),color=col,ls='--',label=method);continue
  rr.sort(key=lambda r:float(r['gamma']));axs[0,j].plot([float(r['gamma']) for r in rr],[float(r['final_Phi']) for r in rr],marker='o',ms=3,color=col,label=method)
  rr=[r for r in rr if float(r['gamma'])>0];axs[1,j].loglog([float(r['gamma']) for r in rr],[float(r['mean_squared_residual']) for r in rr],marker='o',ms=3,color=col)
 axs[0,j].set_title(ds.title());axs[0,j].set_xlabel('Gamma');axs[1,j].set_xlabel('Gamma');axs[0,j].grid(alpha=.2);axs[1,j].grid(alpha=.2)
axs[0,0].set_ylabel('Final worst-group cost Phi');axs[1,0].set_ylabel('Mean squared snapping residual');axs[0,0].legend(frameon=False,fontsize=7);fig.suptitle('P4: fixed unique-source cohorts, k=8, seed=42');save(fig,'corrected_p4.pdf')
trials=rows(next((R/'evidence/original_p2_p3').rglob('trials.csv')));methods={'none':('Direct','#d37928'),'basic':('Basic','#327db1'),'runnerup':('Runner-up','#388f71')}
for filename,keys,labels,title in [('corrected_p3_timing.pdf',['paired_algorithm_ratio','paired_end_to_end_ratio'],['Fresh / method (algorithm)','Fresh / method (comparable E2E)'],'P3: measured timing ratios'),('corrected_p3_coverage.pdf',['attempted_acceptance','effective_saved_coverage'],['Attempted acceptance P/A (%)','Effective saved coverage S/N (%)'],'P3: certificate coverage')]:
 fig,axs=plt.subplots(2,1,figsize=(9,5.3),sharex=True,layout='constrained')
 for i,(key,label) in enumerate(zip(keys,labels)):
  for offset,(method,(name,col)) in enumerate(methods.items()):
   rr=[r for r in trials if r['method']==method and r[key]!=''];axs[i].scatter([int(r['design_index'])+(int(r['seed'])-2)*.035+(offset-1)*.11 for r in rr],[float(r[key])*(100 if 'coverage' in filename else 1) for r in rr],s=11,color=col,label=name,alpha=.85)
  axs[i].set_ylabel(label);axs[i].grid(alpha=.2)
  if 'timing' in filename:axs[i].set_yscale('log');axs[i].axhline(1,color='#555555',ls='--',lw=.8)
 axs[0].legend(frameon=False,ncol=3);axs[0].set_title(title);axs[1].set_xlabel('Frozen design ID (five seeds, small display offsets)');save(fig,filename)
print('Replotted 4 original-experiment figures from frozen CSVs; portable style.')
