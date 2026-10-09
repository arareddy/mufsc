from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'scratch/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
rows=json.loads((ROOT/'SUMMARY.json').read_text())['dataset_steps']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(1,3,figsize=(8.8,3.1),layout='constrained')
for ax,dataset in zip(axes,('adult','bank','credit')):
 selected=[r for r in rows if r['dataset']==dataset]
 for key,color,label,marker in [('request_seconds','#1764AB','Matched model output','o'),('operational_seconds','#BE5C17','With buffered persistence','s')]:
  x=[r['step'] for r in selected];y=[r[f'cumulative_{key}_ratio'] for r in selected]
  lo=[r[f'cumulative_{key}_ratio_seed_min'] for r in selected];hi=[r[f'cumulative_{key}_ratio_seed_max'] for r in selected]
  ax.fill_between(x,lo,hi,color=color,alpha=.13,linewidth=0)
  ax.plot(x,y,color=color,marker=marker,markersize=4,linewidth=1.5,label=label)
  ax.annotate(f'{y[-1]:.2f}x',(3,y[-1]),xytext=(-4,8 if key=='request_seconds' else -13),textcoords='offset points',ha='right',fontsize=8,color=color)
 ax.set_title(dataset.title(),fontweight='bold');ax.set_xticks([1,2,3]);ax.set_xlim(.85,3.15)
 ax.set_ylim(0,max(r['cumulative_request_seconds_ratio_seed_max'] for r in selected)*1.18)
 ax.yaxis.set_major_locator(MaxNLocator(5));ax.grid(axis='y',alpha=.22);ax.set_xlabel('Completed client withdrawals')
axes[0].set_ylabel('Cumulative fresh / compact time')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='outside upper center',ncol=2,frameon=False)
fig.supxlabel('Lines: ratios of summed times. Shading: five-seed range, not a confidence interval. Three timing repeats per sequence.',fontsize=7)
out=ROOT/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'sequence_cumulative.pdf',bbox_inches='tight')
fig.savefig(out/'sequence_cumulative.png',dpi=200,bbox_inches='tight')
plt.close(fig)
print('Figure saved')
