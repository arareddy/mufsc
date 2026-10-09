"""Exact reaggregation of saved group-quality and matched-start evidence."""
from pathlib import Path
from fractions import Fraction as F
import csv,json,statistics

def run(root,out):
 def rows(study,name):return list(csv.DictReader((root/'evidence'/study/'tables'/name).open()))
 counts={};summaries=[]
 for study,name,extra in [('Group_Quality','case_quality.csv',[]),('Lloyd_Comparison','quality.csv',['method'])]:
  rr=rows(study,name);groups={}
  for row in rr:
   a,b=F(row['Phi_A_exact']),F(row['Phi_B_exact']);n0=int(row.get('n0',row.get('n_group0')));n1=int(row.get('n1',row.get('n_group1')))
   assert F(row['Phi_exact'])==max(a,b) and F(row['G_exact'])==a+b
   assert F(row['pooled_SSE_exact'])==n0*a+n1*b
   assert F(row['population_average_exact'])==(n0*a+n1*b)/(n0+n1)
   key=tuple(row[k] for k in ['population','dataset','T',*extra]);groups.setdefault(key,[]).append(row)
  for row in rows(study,'summary.csv'):
   key=tuple(row[k] for k in ['population','dataset','T',*extra]);values=[F(x[row['metric']+'_exact']) for x in groups[key] if x.get(row['metric']+'_exact') not in ('','undefined',None)]
   if not values:continue
   mean=sum(values)/len(values);var=sum((x-mean)**2 for x in values)/(len(values)-1) if len(values)>1 else F(0)
   assert mean==F(row['mean_exact']) and var==F(row['sample_variance_exact'])
   summaries.append({'study':study,'key':key,'metric':row['metric'],'n':len(values),'mean_exact':str(mean),'sample_variance_exact':str(var)})
  counts[study]=len(rr)
 # Paired relative differences are averaged within seed before cross-seed aggregation.
 paired=rows('Lloyd_Comparison','paired_methods.csv');groups={}
 for row in paired:groups.setdefault(tuple(row[k] for k in ['population','dataset','T','metric']),[]).append(row)
 for row in rows('Lloyd_Comparison','paired_methods_summary.csv'):
  group=groups[tuple(row[k] for k in ['population','dataset','T','metric'])]
  for key in ['fair_minus_lloyd','relative_difference']:
   values=[F(x[key+'_exact']) for x in group if x[key+'_exact'] not in ('','undefined')]
   if values:assert sum(values)/len(values)==F(row[key+'_mean_exact'])
 (out/'quality-reaggregated.json').write_text(json.dumps(summaries,indent=2)+'\n')
 return {'quality_rows_verified':counts,'exact_summary_rows':len(summaries),'paired_Lloyd_summary_rows':len(groups)}
