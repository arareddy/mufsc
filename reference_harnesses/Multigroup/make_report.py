"""Build narrative tables only from the verified compact CSVs."""
from common import *
from fractions import Fraction as F
import csv,statistics as st

def read(name):return list(csv.DictReader((ROOT/'tables'/name).open()))
def mean(rows,key):return st.mean(float(x[key]) for x in rows)
def fmt(x,d=3):return f'{x:.{d}f}'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',*['| '+' | '.join(map(str,row))+' |' for row in rows]])
def main():
    v=json.loads((ROOT/'VERIFICATION.json').read_text());assert v['status']=='PASS'
    grid=json.loads((ROOT/'FROZEN_GRID.json').read_text());quality=read('quality.csv');group=read('group_quality.csv');raw=read('raw_timings.csv');pairs=read('paired_ratios.csv');agg=read('aggregate_timings.csv');summary=read('quality_summary.csv');opt=read('optimization.csv');prep=read('preparation.csv');growth=read('growth_summary.csv');noise=read('case_method_timings.csv')
    names=['White alone','Black or African American alone','American Indian alone','Alaska Native alone','American Indian / Alaska Native specified or unspecified (code 5)','Asian alone','Native Hawaiian / other Pacific Islander alone','Some other race alone','Two or more races']
    memberships=table(['RAC1P / group ID','Category','Original','Removed','Retained'],[[f'{g+1} / {g}',names[g],grid['group_counts'][g],grid['removed_counts'][g],grid['retained_counts'][g]] for g in range(9)])
    timing_rows=[]
    for T in (0,1,2):
        for method in (['direct','compact'] if T==0 else ['direct']):
            a=next(x for x in agg if int(x['T'])==T and x['method']==method)
            fr=[x for x in raw if int(x['T'])==T and x['method']=='fresh'];rr=[x for x in raw if int(x['T'])==T and x['method']==method]
            timing_rows.append([T,method,fmt(mean(fr,'algorithm_seconds')),fmt(mean(rr,'algorithm_seconds')),fmt(mean(fr,'request_seconds')),fmt(mean(rr,'request_seconds')),fmt(float(a['algorithm_total_ratio']),2)+'x',fmt(float(a['request_total_ratio']),2)+'x',fmt(float(a['request_min']),2)+'–'+fmt(float(a['request_max']),2)+'x'])
    timing=table(['T','Replay','Fresh alg s','Replay alg s','Fresh request s','Replay request s','Alg total ratio','Request total ratio','Five-seed request-ratio range'],timing_rows)
    quality_table=table(['T','Mean Phi','Sample SD','Seed range'],[[r['T'],fmt(float(r['Phi_mean'])),fmt(float(r['Phi_sd'])),fmt(float(r['Phi_min']))+'–'+fmt(float(r['Phi_max']))] for r in summary])
    groups_table=table(['RAC1P','Retained n_g','Mean cost T0','Mean cost T1','Mean cost T2'],[[g+1,grid['retained_counts'][g],*[fmt(mean([r for r in group if int(r['group_id'])==g and int(r['T'])==T],'cost')) for T in (0,1,2)]] for g in range(9)])
    setup=table(['T','Original training s (mean)','Input load + verify ms (mean)','DIRECT state MiB'],[[T,fmt(mean([r for r in prep if int(r['T'])==T],'original_training_seconds')),fmt(1000*mean([r for r in prep if int(r['T'])==T],'load_verify_seconds'),2),fmt(mean([r for r in prep if int(r['T'])==T],'DIRECT_state_pickle_bytes')/2**20,3)] for T in (0,1,2)])
    growth_table=table(['m','Nonempty slices','Anchor slots','Count cells','T0 setup ms','Compaction ms','Compact bytes','DIRECT state bytes'],[[r['m'],r['slices'],r['anchors'],r['count_cells'],fmt(1000*float(r['train_seconds_mean']),2),fmt(1000*float(r['compaction_seconds_mean']),3),r['compact_pickle_bytes'],r['DIRECT_state_pickle_bytes']] for r in growth])
    components=table(['T','Fresh local + encoding ms','DIRECT metadata ms','DIRECT server table + sampling ms','DIRECT assignment/statistics ms','DIRECT solver ms'],[[T,
        fmt(1000*(mean([r for r in raw if int(r['T'])==T and r['method']=='fresh'],'component_local_summaries')+mean([r for r in raw if int(r['T'])==T and r['method']=='fresh'],'component_encoding')),2),
        fmt(1000*mean([r for r in raw if int(r['T'])==T and r['method']=='direct'],'component_metadata'),3),
        fmt(1000*(mean([r for r in raw if int(r['T'])==T and r['method']=='direct'],'component_table')+mean([r for r in raw if int(r['T'])==T and r['method']=='direct'],'component_server_seed')),2),
        fmt(1000*mean([r for r in raw if int(r['T'])==T and r['method']=='direct'],'component_assignment_stats'),2),fmt(1000*mean([r for r in raw if int(r['T'])==T and r['method']=='direct'],'component_solver'),2)] for T in (0,1,2)])
    unique=[r for r in opt if r['T']=='2'];gaps=[float(r['gap']) for r in unique];rel=[float(r['relative_gap_to_primal']) for r in unique]
    bounds_table=table(['Seed','Round','Returned fixed-partition Phi','Exact dual lower bound (display)','Certified absolute gap','Gap / primal'],[[r['seed'],r['round'],fmt(float(r['Phi_fixed_partition']),6),fmt(float(r['D']),6),fmt(float(r['gap']),6),fmt(100*float(r['relative_gap_to_primal']),3)+'%'] for r in unique])
    q={(r['seed'],r['T']):float(r['Phi']) for r in quality};gain=[1-q[str(s),'2']/q[str(s),'0'] for s in range(10000,10005)]
    cv=table(['T','Method','Within-case request CV range (3 repeats)'],[[T,method,fmt(100*min(float(r['request_seconds_CV']) for r in noise if int(r['T'])==T and r['method']==method),2)+'–'+fmt(100*max(float(r['request_seconds_CV']) for r in noise if int(r['T'])==T and r['method']==method),2)+'%'] for T in (0,1,2) for method in (['fresh','direct','compact'] if T==0 else ['fresh','direct'])])
    p0=[r for r in prep if r['T']=='0'];lock=v['lock_summary']
    report=f'''# Multi-group whole-client replay: implemented prototype and bounded pilot

Completed 26 September 2026. Numerical map **FTF-MG-FW12-B6-v1**; run **multigroup-20260926-v1**. This is a separate, self-validated prototype. It implements disjoint categorical m-group summaries, exact statistics/objectives, a deterministic guarded multi-group updater, matched whole-client DIRECT replay for T=0,1,2, and compact T0 replay. All requested stages completed; no solver-reliability blocker remains for this bounded grid. Independent review is still required.

The synthetic oracle checks passed, and all **35 real-data gate models plus 105 timed models** satisfy the full exact indexed comparisons. The pilot uses **nine documented ACS race categories**, because authoritative Adult race labels could not be established from the available processed artifact. Mean worst-group cost falls from **16.374 at T0 to 9.445 at T2**. Matched total resident request-time ratios are **138.70x DIRECT / 139.14x compact at T0**, **1.60x DIRECT at T1**, and **1.30x DIRECT at T2**. These figures do not compare unlike training budgets and do not replace any binary panel.

## What the implementation contributes

The current manuscript already has the zero-quantization O(m log^2 k) warm-start extension (app:m-warm) and the fixed-partition epigraph/dual/guard formulation (app:multi-group). Ghadiri et al. already develops socially fair clustering for m groups and explicitly warns that the primal value composed with simplex weights need not be convex or quasiconvex ([Section 3](https://doi.org/10.1145/3442188.3445906)). Pan et al. already handles whole-client deletion by removing client contributions and updating the server ([Section 5.3 / Algorithm 4](https://openreview.net/forum?id=VzwfoFyYDga)). No invention of multi-group fair clustering, new centralized approximation factor, or new general unlearning theorem is claimed here.

The additive module multigroup.py uses the unchanged, hash-verified 17-file FTF-1D primitive set. It generalizes all group-indexed arrays and counts, exact rational h/n_g weights, persistent-ID streams, N/S/SS and Phi=max_g Phi_g (with G=sum_g Phi_g separately). Local absent groups are omitted. All declared global groups must remain nonempty. Empty means are never evaluated; invalid deletions fail. Canonical saturation, zero-mass completion, snapping, indexed ties and optional guarded anchor Lloyd are preserved.

Whole-client deletion leaves every surviving ordered slice and keyed stream unchanged. Reusing its summary, subtracting exact counts, rebuilding weights and rerunning the server therefore produces fresh C0. Identical refinement inputs then yield identical assignments, exact integer moments and deterministic updates by induction. DIRECT avoids surviving-local reseeding and uses read-only surviving coordinate views; it recomputes every positive-round assignment/moment. Compact T0 receives only IDs and trusted small state. THEORY.md gives the conditional functional proof and the compact sequence invariant.

## Frozen real population and membership

Adult's supplied artifact contains full_data, sex masks and client arrays, but no saved feature-name/category schema or raw race labels. Its preparation script alone does not identify every standardized dummy column. No one-hot guesses or new download were used.

The alternate ACS source has a frozen ordered 16-feature schema, saved binary64 mean/std, and unquantized standardized arrays. RAC1P is documented column 15 (zero based). For codes 1..9, recomputing (code-mean)/std produces nine distinct binary64 levels; **every one of 100,000 rows equals exactly one level**, with zero unmatched rows and no tolerance. The original fine-grid encoding matches all saved encoded integers. The original sex column is also checked against saved group labels. Offsets, saved source-row arrays, population metadata and every native-ID CSV row agree; all 100,000 native IDs are unique. INPUTS.json binds files, levels and the complete ordered membership hash; IDENTITY_REGISTRY.json binds each client's original ordered rows and race memberships. This is recovery from the documented numeric schema and immutable processed data, not a new verification of the original Census CSV bytes.

The population is the smallest existing expanded ACS choice, n100000_C10, with the original 16 feature columns and standardization, clip=8, b=12, gamma=0, no anchor Lloyd. RAC1P **remains an input feature**. No refit, feature exclusion, population resampling or survey weighting occurs. This is a selected finite 10-state-client sample, not a nationally representative race-fairness estimate. Category names follow the [official 2018 RAC1P dictionary](https://api.census.gov/data/2018/acs/acs1/pums/variables/RAC1P.json); code 5 specifically includes American Indian and Alaska Native tribes specified, or American Indian/Alaska Native unspecified with no other races.

{memberships}

The request removes persistent **client 1 (Missouri), 6,799 rows / 6.799%**, leaving **93,201** rows. It was selected before outcomes as the valid client closest to original median size, tie by persistent ID. It is the same request at all five training seeds 10000–10004, k=10 and T=0,1,2. All nine groups remain nonempty; the seven-row category stays in the objective. That tiny category and other small groups limit any general fairness interpretation. Original nonempty slices/anchor slots are 82/721; after deletion they are 74/648.

FROZEN_GRID.json SHA-256: `{sha(ROOT/'FROZEN_GRID.json')}`. All cases, outcomes and repetitions were retained. There were **no exclusions, failed workers, numerical mismatches, selected reruns or parameter tuning**.

## Correctness and independent arithmetic scope

- 120 T0 fresh/summary-reuse comparisons at m=3,5 against a separately written scalar rational oracle, plus 54 sequential compact-state steps. All exact center bytes, summary values, persistent owners and rational weights agree. Tests cover mixed and locally absent groups, persistent-ID gaps, empty clients, one-record boundaries, coincident coordinates, zero potential/multiplicity, saturation, snap ties and optional anchor Lloyd.
- 48 T1/T2 fresh/DIRECT comparisons on the same small families (two seeds, one prespecified valid whole client per family), with independent scalar assignments, moments and pointwise objectives. 271 malformed/domain/global-empty rejection checks pass. Access traps prohibit surviving local reseeding and raw access during compaction; compact array copies are independent and read-only.
- Six separate exact primal interval-reference cases, including inactive groups, zero dual denominators, fully empty clusters and ties, all reached bracket width <=1/100000 (several exactly). Known analytic optima are checked. The finite production solver is **not** required to attain those optima; for example it correctly rejects its worse candidate when the incumbent is already optimal. The primal oracle imports no production arithmetic. Shared PCG64/SeedSequence and runtime binary64 conversion remain disclosed.
- Three tiny binary **T0 only** seed comparisons match canonical initializers. This is not full binary regression coverage; positive-round binary identity is not asserted.
- Real gates: 20 replay-versus-fresh comparisons across 35 gate models. All 105 timed outputs equal their exact gate model and associated summary/solver values. No tolerance or center permutation is used. At T0 the statistic list is empty; positive rounds compare every N/S/SS integer.
- The separate saved-evidence verifier checks 290 indexed center arrays and 135 moment triples including original-population setup models, exact Phi=max and G=sum, all expected keys, budget-prefix equality and timing sums/orders. It independently recalculates **{v['dual_candidate_certificates_rederived']} stored candidate dual certificates** across 15 update records (10 distinct seed/round partitions). It does not independently reassign every real raw row; real replay comparisons share the production kernel. CORRECTNESS.json and VERIFICATION.json identify these scopes distinctly.

No prior binary candidate's independent sign-off is inherited. These are self-validation checks for review.

## Solver specification and optimization quality

The solver starts at uniform simplex weights, evaluates all vertices, and runs at most 12 exact Frank-Wolfe direction steps on the **concave dual**, each with six dyadic derivative-bisection evaluations. Exact zero direction gap terminates early; otherwise the fixed budget includes stalls. Directions and ties are deterministic. The best exact dual bound is retained over all evaluated points. Each exact weighted mean is rounded once to binary64. Zero weighted denominators use the sole occupied group mean, otherwise the incumbent; fully empty centers stay indexed.

The best represented candidate is selected by exact fixed-partition Phi, then lexicographic rational lambda; an exact <= incumbent guard controls acceptance. Returned-center objectives, not ideal unrounded objectives, define nonincrease. The valid absolute gap is returned fixed-partition Phi minus the best exact D. No exact optimization claim or global clustering-optimum claim follows from a small gap. G is never substituted for Phi.

All 10 distinct real updates accepted the candidate and reached the fixed iteration bound. Certified absolute gaps range **{min(gaps):.6f}–{max(gaps):.6f}**, or **{100*min(rel):.3f}%–{100*max(rel):.3f}% of the returned fixed-partition primal value**. No gap acceptance threshold was used, and the solver was not tuned after outcomes.

{bounds_table}

The table concerns the partition before each update. Nearest reassignment after the update may lower costs further; these fixed-partition primal values are therefore different from final nearest-center quality below. Exact fractions, candidate traces, branches, guard decisions and all statistics are saved under each gate.

## Matched resident request timings

Algorithm time encloses the whole public call, including validation, allocations, encoding/local seeding for fresh, metadata/reuse for replay, server sampling, all refinement and exact guard/gap calculations. Request time additionally includes survivor dictionary preparation and identical model-witness serialization/local write without fsync. Inputs and initial state are resident. Loading, startup, original training, compact preparation, state serialization, quality and verification are outside the request and reported separately. No physical federation, cold-storage, network, checkpoint persistence or erasure latency is measured.

At T0, [fresh,direct,compact] rotates over three repetitions so every method occupies each position once per seed. With two methods and three repeats, per-case first-position counts must be 2:1; alternating orders give complementary balance across T1/T2 and exact overall first-position balance across those budgets. Each individual positive budget has 8:7 first-position counts over five seeds. The small growth probe also has imperfect order balance (three rotations of four m values). These limitations were specified before measurement.

{timing}

All 20 seed/method/budget pairs favor replay in algorithm and request time. Ratios of total times are shown above; five-seed mean paired ratios, sample SD, min/max, every loss/tie count and all raw seconds are in tables/. Timing repeats are technical measurements, **not 15 independent scientific trials per budget**. T0 direct and compact latencies are effectively the same on this optimized whole-client path; there is no supported additional compact runtime advantage. Compact's benefit here is the smaller retained state and raw-free API. The large T0 ratio reflects a small compact server versus local processing of 93,201 survivor rows on this chosen 10-client population; it is not a universal speed factor.

{components}

These nonoverlapping component means explain why positive-round gains shrink: DIRECT still pays for all retained assignments/statistics and the exact rational solver. The solver is the largest measured positive-round component. Exact-gap/trace construction is part of this prototype's cost; an optimized implementation would require a new matched measurement contract.

{cv}

Only three repeats were used; millisecond-scale T0 replay remains sensitive to desktop load. Lock receipts cover all 16 pilot/growth batches: total held time **{lock['held_seconds']:.3f}s**, queue wait **{lock['wait_seconds']:.6f}s**, one-minute loads **{lock['one_minute_load_min']:.2f}–{lock['one_minute_load_max']:.2f}**. The parent held exclusive flock across one worker per batch, then released it. All five numerical thread environment controls were one; native pool sizes were not independently enumerated (threadpoolctl absent). Active uarpd, WebKit, WindowServer and other desktop processes are logged. The advisory lock cannot eliminate unrelated load. There is no dedicated-host causal speedup claim.

## Retained-population quality

Phi is maximum group-average nearest-center squared cost, computed exactly on the same fixed-point represented survivors and then displayed as a float. Each seed contributes once per T. G is the unweighted sum of group-average costs; pooled SSE is separately weighted by n_g. Exact fractions are retained.

{quality_table}

The mean paired T0-to-T2 decrease is **{100*st.mean(gain):.1f}%**, seed range **{100*min(gain):.1f}%–{100*max(gain):.1f}%**. No quality adequacy threshold was specified. This does not establish downstream, individual, intersectional or population fairness. It also does not compare a binary objective with the new nine-group objective.

{groups_table}

Mean of each seed's maximum differs from the maximum of the group means in this table; aggregation is not interchanged. The seven-row group is included without reweighting, merging or a favorable-case exclusion.

## Setup, state and growth with m

{setup}

Mean extra T0 compaction is **{1000*mean(p0,'compaction_seconds'):.3f} ms**. The serialized compact state is **{int(mean(p0,'compact_pickle_bytes')):,} bytes** ({mean(p0,'compact_pickle_bytes')/2**20:.3f} MiB); the original DIRECT state is **{int(mean(p0,'DIRECT_state_pickle_bytes')):,} bytes** ({mean(p0,'DIRECT_state_pickle_bytes')/2**20:.3f} MiB). These are protocol-5 pickle sizes measured in memory, not measured RAM or disk savings. No large state pickle was saved. Setup is a real cost, separate from the resident request ratios; it is not amortized into a production service claim.

The prespecified growth probe fixes 1,080 dyadic rows, six persistent clients, d=4, k=10 and seed7, changing only synthetic category membership g=local_row mod m. It uses the same rows and three recorded repetitions per m. These are administrative scaling fixtures, not additional real populations or comparable fairness panels.

{growth_table}

Slots and count cells increase exactly linearly here because every slice has at least k rows; setup time need not be monotone (m=3 is faster than m=2 in this small run). At most C*m*k slots are retained generally, with saturation reducing that bound. Per-round statistics occupy m*k*(d+2) Python integers: 1,620 for the real pilot. Exact bit lengths and the solver's m+1+72 maximum candidate count add costs beyond a numeric-entry count. THEORY.md gives the resource scope; no universal wall-time scaling law is inferred from four small settings.

## Deliverables, claims and limitations

Proved under the stated fixed-map/trusted-state assumptions: same-seed whole-client model replay, compact T0 sequence invariant, exact weak-duality fixed-partition gap, and nonincreasing nearest-center Phi after the represented guard. Tested: the bounded fixtures, the one ACS population/request/five-seed grid and all saved equality/certificate/aggregation checks. Conditional: initialization approximation retains the existing manuscript's ideal-tape assumptions; same-seed law equality is limited to the stated request dependence. Unresolved: independent review, global optimum, broad utility adequacy, other group attributes/populations, record deletion/certificate heuristics, hostile mutable state, cross-platform bit reproducibility, deployed/durable costs and erasure.

REPORT.md, PROTOCOL.md, THEORY.md, INTEGRATION_NOTES.md and APPENDIX_PROPOSAL.tex explain the scope. multigroup.py is the additive variant; oracle.py/tests, CORRECTNESS.json and VERIFICATION.json hold self-validation. INPUTS.json/IDENTITY_REGISTRY.json/source snapshots bind the data and reading context. tables/ contains compact machine-readable measurements. runs/ preserves full model/statistic/solver witnesses and lock/load receipts. REPRODUCE.md and verify_handoff.py provide checks and commands. READY_FOR_REVIEW.json binds the frozen handoff and explicitly is not an independent approval.

No canonical code, T0 deliverable, frozen experiment, historical Git pointer, live manuscript or Overleaf state was modified. The separate positive-refinement task's unfinished results were not consumed. No subagent, further task, usage reset, data download, bulk archive, iCloud export, upload or publication was used. New artifacts remain local and require a separately chosen backup.
'''
    (ROOT/'REPORT.md').write_text(report)
    write_json(ROOT/'REPORTING_SUMMARY.json',{'source_verification_sha256':sha(ROOT/'VERIFICATION.json'),'quality':summary,'timing':agg,'fixed_partition_gap_min':min(gaps),'fixed_partition_gap_max':max(gaps),'mean_paired_T0_T2_Phi_decrease':st.mean(gain),'counts':{'synthetic_T0':120,'synthetic_positive':48,'sequence_steps':54,'invalid':271,'real_gates':35,'real_timed':105}})
    print('REPORT.md written from verified tables')
if __name__=='__main__':main()
