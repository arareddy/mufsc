from common import *
import csv
read=lambda n:list(csv.DictReader((W/'tables'/n).open()))
s=read('summary.csv');ps=read('paired_methods_summary.csv');inc=read('step_increases.csv');v=load(W/'VERIFICATION.json')
logs=[json.loads(x) for x in (W/'LOCK_RECEIPTS.jsonl').read_text().splitlines()]
case_batches={x['batch'] for x in logs if x['event']=='queued' and any(a.endswith('/worker.py') for a in x['command'])}
case_wait=sum(x['wait_seconds'] for x in logs if x['batch'] in case_batches and x['event']=='acquired');case_held=sum(x['held_seconds'] for x in logs if x['batch'] in case_batches and x['event']=='released')
def summary(pop,ds,m,t,k):return next(r for r in s if (r['population'],r['dataset'],r['method'],int(r['T']),r['metric'])==(pop,ds,m,t,k))
def fmt(r):return f"{float(r['mean']):.3f} +/- {float(r['sample_sd']):.3f}"
text=['# Matched-start ordinary Lloyd versus guarded fair refinement\n',
'**Complete: all 30 frozen cases passed, with no exclusions or unresolved correctness issue.** Both methods start from identical indexed fair-initialized centers on the same survivors. At T=1 and T=2, fair refinement has lower worst-group cost in all 15 record-deletion cases and all 15 whole-client-deletion cases. At each budget it also has higher population-average cost and higher group 1 cost in every case. The result supports an objective tradeoff, not simultaneous improvement of all groups.\n',
'## What was executed\n',
'Two separate populations x Adult/Bank/Credit x seeds 10000-10004; k=10; T=0,1,2 **refinement rounds**. Record cases retain their original 30/45/30-record requests; whole-client cases retain their one prespecified client0 request (300/2259/299 records). No populations, requests, seeds or parameters changed. Fixed group semantics: Adult 0=complement of stored male mask, 1=male mask; Bank 0=not married, 1=married; Credit 0=other stored education codes, 1=EDUCATION in {1,2}. Adult/Credit upstream raw-provenance limitations remain.\n',
'Lloyd is a separate unweighted-mean update with exact integer sums, one binary64 rounding of each rational mean, indexed nearest-center ties, and unchanged empty centers. It has **no acceptance guard**. Both methods use the same represented coordinates; updated centers are not snapped back to the data grid. Fair refinement uses the unmodified canonical learner. Details and the independently written scorer are in NUMERICAL_CONTRACT.md. This isolates update choice conditional on FTF initialization; it is not an end-to-end ordinary-k-means baseline, initialization comparison, runtime benchmark or new unlearning result.\n',
'## Paired quality differences\n',
'Each percentage below is first computed within a seed as 100*(fair-Lloyd)/Lloyd, then averaged over five seeds. Negative favors fair for the indicated cost. Values show mean +/- sample SD [min, max], not confidence intervals. T0 differences are exactly zero by construction.\n',
'| Population | Dataset | T | Worst-group Phi difference (%) | Population-average difference (%) |\n|---|---|---:|---:|---:|']
for pop in ['record','client']:
 for ds in ['adult','bank','credit']:
  for T in [1,2]:
   cells=[]
   for k in ['Phi','population_average']:
    r=next(r for r in ps if (r['population'],r['dataset'],int(r['T']),r['metric'])==(pop,ds,T,k));cells.append(f"{100*float(r['relative_difference_mean']):+.2f} +/- {100*float(r['relative_difference_sample_sd']):.2f} [{100*float(r['relative_difference_min']):+.2f}, {100*float(r['relative_difference_max']):+.2f}]")
   text.append(f'| {pop} | {ds.title()} | {T} | '+' | '.join(cells)+' |')
text += ['\nAt T2 the mean paired worst-group reductions are 4.75%/3.15%/5.07% for record deletions and 3.92%/4.24%/4.93% for whole-client deletions (Adult/Bank/Credit). Corresponding population-average increases are 4.72%/0.55%/0.71% and 4.47%/1.87%/0.53%. These are descriptive results on these cases, not universal bounds. Group 0 improves and group 1 worsens relative to Lloyd in every positive-budget case; group 1 is the larger retained group in these datasets. This does not imply every demographic setting behaves similarly.\n',
'## Absolute quality at every budget\n',
'Five-seed mean +/- sample SD. Phi is computed as max(Phi_0,Phi_1) **inside each seed** before averaging. Population mean is (n0*Phi_0+n1*Phi_1)/(n0+n1), again computed before seed averaging. G is the sum of group means; pooled SSE is the count-weighted sum and has a distinct scale. Exact per-case fractions, all ranges and all six metric summaries are in the CSVs. Shared T0 is printed once.\n']
for pop in ['record','client']:
 text += [f'### {"Record-deletion" if pop=="record" else "Whole-client-deletion"} survivors\n','| Dataset | T | Update | Group 0 | Group 1 | Phi | Population mean |\n|---|---:|---|---:|---:|---:|---:|']
 for ds in ['adult','bank','credit']:
  for T in [0,1,2]:
   for m in (['fair'] if T==0 else ['fair','lloyd']):
    label='shared' if T==0 else m
    text.append(f'| {ds.title()} | {T} | {label} | '+' | '.join(fmt(summary(pop,ds,m,T,k)) for k in ['Phi_A','Phi_B','Phi','population_average'])+' |')
 text.append('')
text+=['## Every unfavorable stepwise exception\n',
'The following are all increases among the four primary costs over adjacent steps; all occur at T1->T2. No T0->T1 increase occurs. Fair has five group-1 increases and two population-average increases; Lloyd has one group-0/worst-group increase. Pooled SSE duplicates the two fair population-average increases under fixed counts. Full exact changes, before/after costs and endpoint comparisons are preserved in `within_method_changes.csv` and `step_increases.csv`.\n',
'| Population | Dataset | Seed | Method | Metric | Absolute increase | Relative increase |\n|---|---|---:|---|---|---:|---:|']
for r in inc:
 if r['metric'] in ['Phi_A','Phi_B','Phi','population_average']:
  text.append(f"| {r['population']} | {r['dataset'].title()} | {r['seed']} | {r['method']} | {r['metric']} | {float(r['change']):.6f} | {100*float(r['relative_change']):.4f}% |")
text += ['\nLloyd pooled SSE decreased in all 60 adjacent case steps; fair Phi decreased in all 60. These are observed exact-fraction checks, not a broad convergence theorem. At matched positive budgets there is no exception to lower fair Phi or to higher fair population cost; the latter is an unfavorable result for total distortion and is retained, not hidden. G favors fair in 15/30 cases at T1 and 14/30 at T2; it must not be relabeled as Phi.\n',
'## Interpretation for the paper\n',
'This adds the previously missing controlled **update-choice comparator**. From the same FTF-initialized centers, minimizing ordinary population-weighted distortion can leave higher worst-group cost than guarded fair refinement. It therefore strengthens motivation for declaring a worst-group objective when that is the application aim. It also makes the tradeoff explicit: group 1 and total population distortion are worse under fair refinement here. The evidence supports a choice between objectives, not a claim that the method improves everyone, equalizes costs, reaches a global optimum, or beats optimized conventional k-means from its own initialization. No quality-adequacy threshold was supplied.\n',
'## Newly executed verification and inherited scope\n',
'New checks: seven fixed fixtures (five direct scalar Fraction trajectory/objective fixtures, including unequal groups, genuine tradeoff, ties, duplicates, empty clusters and thirds; two exact halfway binary64 aggregate fixtures); 30 full-population reruns; all 90 saved fair center/statistic prefixes reproduced exactly; all 90 saved fair objective sets recomputed; 150 independently scored center tuples agreed exactly with canonical objectives and full nearest-center label arrays; same indexed C0 and first-round statistics for each method pair; actual retained group counts and ordered row-identity hashes; all 209 input files and 27 frozen source files unchanged. Real-data independent assignment intervals resolved all points without fallback; fixtures exercised ambiguity and exact tie fallback. There were no failed cases, retries, exclusions, or scientific source changes after freeze.\n',
'The independent scorer computes new assignments and group objectives from represented records; it does not import production assignment/objective/accumulator functions. Its scalar test oracle sums pointwise rational squared distances. Shared Python/NumPy and binary64 conversion remain a dependency; this is separately written executed checking, not independent human validation. Canonical numerical-kernel guarantees and the original arithmetic gate are inherited source-bound evidence, distinct from the new reproduction checks. Whole-client T0 unlearning review scope is unchanged. No full-cache equality, erasure or adaptive fresh-independent guarantee follows for Lloyd.\n',
f'All substantial work held the required parent-owned exclusive flock, with one numerical worker and five library thread limits set to one. Each of the 30 case batches released the lock before the next. Case queue wait totaled {case_wait:.4f} s; lock-held work totaled {case_held:.3f} s, including data validation, both variants, independent scoring and output. These are operational accounting, not algorithm timing comparisons. Load/process snapshots and separate queue/acquire/release receipts are in LOCK_RECEIPTS.jsonl; unrelated desktop load remains uncontrolled. Rendering is also locked.\n',
'## Deliverables and stop\n',
'One visually checked six-panel PDF in `figures/matched_start_quality.pdf`; `tables/quality.csv`, `summary.csv`, paired/within-method exact tables and summaries, all higher-cost exceptions and mean-vs-max checks; exact centers and N/S/SS in 30 `runs/matched-start-v1/*/outputs.json` files; per-case completion receipts; frozen protocol/grid/input/source manifests; independent fixture receipts; runnable scripts and REPRODUCE.md; concise LaTeX proposal in INTEGRATION_NOTES.md; final verification and file manifest. The figure displays paired relative differences; the absolute values remain above and in tables. All 30 cases, both populations, all seeds and both rounds are preserved.\n',
'The bounded experiment is complete. No manuscript, prior group-quality workspace, canonical source, frozen artifacts or original Git pointer was modified. No data refetch, bulk dataset copy, new environment, task/subagent, usage reset, external share, upload or Overleaf publication. The 11 MB grid retains ordered identity metadata for direct reproducibility, not a copied feature dataset; raw datasets/checkpoints are read in place. Outputs are local-only and need a separately chosen backup. Stop here; no expanded sweep or full conventional baseline was launched.\n']
(W/'REPORT.md').write_text('\n'.join(text))
(W/'INTEGRATION_NOTES.md').write_text(r'''# Integration notes

Proposal only. Do not replace current live manuscript files from this task. No integration or Overleaf push performed.

## Short LaTeX-ready paragraph

To isolate the refinement rule, we compared ordinary Lloyd updates and guarded fair updates from identical FTF-initialized centers on the same retained records, using five seeds for each dataset in the separate record- and whole-client-deletion studies. At both $T=1$ and $T=2$ refinement rounds, fair updates reduced the worst-group cost relative to Lloyd in all 15 cases of each study, while increasing population-average cost and the larger group's cost in every case. At $T=2$, the mean paired reductions in worst-group cost were $4.75/3.15/5.07\%$ for record deletion and $3.92/4.24/4.93\%$ for whole-client deletion (Adult/Bank/Credit); population-average costs increased by $4.72/0.55/0.71\%$ and $4.47/1.87/0.53\%$, respectively. This matched-start comparison illustrates the tradeoff between worst-group and population-average distortion; it does not compare initialization strategies or establish an advantage over fully optimized conventional $k$-means.

## Appendix figure caption

Matched-start refinement quality. Rows show the distinct record-deletion and whole-client-deletion populations; columns show datasets. Each seed's value is $100(c_{\rm fair}-c_{\rm Lloyd})/c_{\rm Lloyd}$ for the indicated cost, so negative values favor fair updates. Thin paths retain all five seeds; bold markers average paired percentages, and bars show one sample standard deviation. The shared fair initialization gives identical $T=0$ costs. Worst-group cost is the maximum of group averages within each seed, and population-average cost weights each group by its retained count. Axis scales differ by dataset. Group meanings are shown above panels. This isolates update choice at $T=1,2$ refinement rounds; absolute costs and exact fractions accompany the figure.

## How the motivation changes

This supplies a controlled comparison that P4's centralized fair initializer did not provide. It gives local empirical support for choosing the worst-group objective when that aim matters, while requiring an explicit statement that the choice worsens population distortion and group 1 here. Preserve the observed five fair group-cost increases and two fair population-cost increases between rounds, plus the one Lloyd worst-group increase. Do not claim coordinatewise improvement, equality/equalization, global optimality, generic demographic advantage, an application threshold, a fully optimized ordinary baseline, or a new Lloyd exact-unlearning guarantee.

Keep both populations separate in numerical tables. The two budget comparisons for a seed are not independent scientific trials; there are five seeds per dataset/population. Use the guarded algorithm name and matched-start qualifier. Technical details (integer sums, representational rounding, interval scorer, hash/identity checks) belong in the technical appendix/report, not the main narrative. Existing fixed-preprocessing and Adult/Credit provenance limitations remain.
'''.replace('\\\\%','\\%'))
print('Report and integration notes written.')
