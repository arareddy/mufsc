"""One-time reporting correction, never invokes a training/measurement worker."""
from pathlib import Path
import json,hashlib,csv,shutil,fcntl
W=Path(__file__).resolve().parent;S=W/'reporting_correction_20260926';S.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with open('/private/tmp/ftf_benchmark_20260926.lock','a+') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
 keep=[*W.glob('*.md'),W/'RESULT_MANIFEST.json',W/'verification.json',W/'figure_validation.json',W/'analyze.py',W/'plot.py',W/'make_report.py',*W.joinpath('tables').glob('*.csv'),*W.joinpath('figures').glob('*.pdf')]
 for p in keep:
  d=S/'superseded'/p.relative_to(W);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
 # Hashes/metadata of all original run evidence, without duplicating it.
 R=W/'runs'/(W/'RUN_ID').read_text().strip()
 raw={str(p.relative_to(W)):dict(sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
 (S/'raw_before.json').write_text(json.dumps(raw,indent=2)+'\n')
 fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
p=W/'analyze.py';s=p.read_text().replace('from pathlib import Path','from pathlib import Path\nfrom fractions import Fraction')
s=s.replace('def validate_array(a):', '''def exact_quality(q):
 v={name:Fraction(q['exact'][name]['numerator'],q['exact'][name]['denominator']) for name in ['Phi_A','Phi_B','Phi','G']}
 assert v['Phi']==max(v['Phi_A'],v['Phi_B']), 'Phi is not the exact max-group cost'
 assert v['G']==v['Phi_A']+v['Phi_B'], 'G is not the exact sum of group-normalized costs'
 assert all(q[name]==float(value) for name,value in v.items()), 'Saved quality float disagrees with exact fraction'
 return v

def validate_array(a):''')
s=s.replace('seen=[];identity=[]','seen=[];identity=[];quality_checks=[]')
s=s.replace("   valid_witness(gw,T,10,inp['d'],n)","""   quality_exact=exact_quality(gm['quality'])
   quality_checks.append(dict(dataset=inp['dataset'],seed=inp['settings']['seed'],T=T,method=m,Phi_numerator=quality_exact['Phi'].numerator,Phi_denominator=quality_exact['Phi'].denominator,Phi_A_numerator=quality_exact['Phi_A'].numerator,Phi_A_denominator=quality_exact['Phi_A'].denominator,Phi_B_numerator=quality_exact['Phi_B'].numerator,Phi_B_denominator=quality_exact['Phi_B'].denominator,sum_group_normalized_costs_numerator=quality_exact['G'].numerator,sum_group_normalized_costs_denominator=quality_exact['G'].denominator,Phi_is_exact_max=True,G_is_exact_sum=True))
   valid_witness(gw,T,10,inp['d'],n)""")
s=s.replace("G=gm['quality']['G'],Phi_A=gm['quality']['Phi_A'],Phi_B=gm['quality']['Phi_B']","Phi=float(quality_exact['Phi']),sum_group_normalized_costs=float(quality_exact['G']),Phi_A=float(quality_exact['Phi_A']),Phi_B=float(quality_exact['Phi_B'])")
s=s.replace("'method','G','Phi_A'","'method','Phi','sum_group_normalized_costs','Phi_A'")
s=s.replace("repetitions_per_key=4,identity_checks=identity", "repetitions_per_key=4,identity_checks=identity,objective_definition='Phi=max(Phi_A,Phi_B); G=Phi_A+Phi_B (sum of group-normalized costs)',exact_quality_definition_checks=len(quality_checks)")
s=s.replace("csvout('raw_observations.csv',raw)","csvout('quality_definition_checks.csv',quality_checks)\ncsvout('raw_observations.csv',raw)")
s=s.replace("G_mean=st.mean(x['G'] for x in rr),G_sd=st.stdev(x['G'] for x in rr),G_min=min(x['G'] for x in rr),G_max=max(x['G'] for x in rr)","Phi_mean=st.mean(x['Phi'] for x in rr),Phi_sd=st.stdev(x['Phi'] for x in rr),Phi_min=min(x['Phi'] for x in rr),Phi_max=max(x['Phi'] for x in rr)")
p.write_text(s)
p=W/'plot.py';s=p.read_text().replace("'G'","'Phi'").replace('Fairness cost G: maximum group-average squared distance','Fairness cost Phi: maximum group-average squared distance');p.write_text(s)
p=W/'make_report.py';s=p.read_text().replace("'G'","'Phi'").replace("'G_mean'","'Phi_mean'").replace("'G_sd'","'Phi_sd'")
s=s.replace('G is the maximum group-average squared nearest-center distance on the fixed-point represented survivors.', 'Phi = max(Phi_A, Phi_B) is the maximum group-average squared nearest-center distance on the fixed-point represented survivors. The saved field G = Phi_A + Phi_B is the sum of group-normalized costs; it is not the fairness objective. Tables explicitly label that auxiliary sum as sum_group_normalized_costs.')
s=s.replace("'## Main finding'", "'**Reporting correction (26 September):** The initial figures and quality summaries mistakenly used saved G (the sum of group-normalized costs) as the worst-group objective. This version uses saved exact Phi throughout. All raw run evidence and timing results are unchanged; see REPORTING_CORRECTION.md.', '', '## Main finding'")
s=s.replace('The independent reporting verifier imports no production training, replay or witness routines.', 'The independent reporting verifier imports no production training, replay or witness routines. It asserts Phi=max(Phi_A,Phi_B) and G=Phi_A+Phi_B using exact saved rational values for all 180 gate outputs, then derives plotted fairness values from the exact Phi fractions. Raw G is retained only under the explicit table label sum_group_normalized_costs.')
s=s.replace('All methods have exactly the same retained-population fairness cost at a matched seed and budget.', 'All methods have exactly the same retained-population worst-group cost Phi=max(Phi_A,Phi_B) at a matched seed and budget.')
needle="(W/'INTEGRATION_NOTES.md').write_text"
insert="""for ds in ['adult','bank','credit']:
 qq=sorted((x for x in q if x['dataset']==ds),key=lambda x:int(x['T']))
 wording.append('')
 wording.append(f\"> On {ds.title()}, the mean retained-population worst-group cost Phi was \"+', '.join(f\"{f(x,'Phi_mean'):.3f}\" for x in qq)+' at T=0,1,2, respectively, across the five seeds. These are maxima of group-average costs, not sums of the two group costs.')
"""
s=s.replace(needle,insert+needle);p.write_text(s)
(W/'REPORTING_CORRECTION.md').write_text('''# Reporting correction: worst-group cost\n\nThe initial REPORT.md and three PDF figures incorrectly treated saved G as the maximum group-average cost. In the unchanged source objective.py, G is the **sum of group-normalized costs** and Phi is **max(Phi_A, Phi_B)**. The saved gate outputs contain both correct exact rational quantities; the defect was in downstream reporting.\n\nThe corrected analysis derives every fairness value from the saved exact Phi numerator/denominator. It asserts both Phi=max(Phi_A,Phi_B) and G=Phi_A+Phi_B with Fraction arithmetic on all 180 gate outputs, and verifies saved float projections. All tables, variability ranges, paired percentage decreases, figure ordinates, captions and integration wording now use Phi. The optional sum is retained only as the explicitly named sum_group_normalized_costs table column. The frozen protocol already specifies the maximum and remains unchanged.\n\nNo new training, timing, quality-evaluation or diagnostic campaign was run. No raw run file, witness, checkpoint, gate output or timing observation was edited. The superseded reporting artifacts are preserved in reporting_correction_20260926/superseded and are not current results. Raw preservation and unchanged timing checks are recorded in reporting_correction_verification.json.\n''')
(W/'REPRODUCE.md').write_text((W/'REPRODUCE.md').read_text()+'''\n## Objective-field correction\n\nUse corrected Phi columns for fairness. Phi is the maximum group-average cost; the original saved G field is the sum of group-normalized costs. quality_definition_checks.csv records exact rational identity checks for every gate output. REPORTING_CORRECTION.md documents the superseded reporting and preservation checks. Original run JSONs are unchanged.\n''')
print('Reporting correction applied; original run evidence preserved')
