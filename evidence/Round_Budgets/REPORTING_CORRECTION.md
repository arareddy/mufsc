# Reporting correction: worst-group cost

The initial REPORT.md and three PDF figures incorrectly treated saved G as the maximum group-average cost. In the unchanged source objective.py, G is the **sum of group-normalized costs** and Phi is **max(Phi_A, Phi_B)**. The saved gate outputs contain both correct exact rational quantities; the defect was in downstream reporting.

The corrected analysis derives every fairness value from the saved exact Phi numerator/denominator. It asserts both Phi=max(Phi_A,Phi_B) and G=Phi_A+Phi_B with Fraction arithmetic on all 180 gate outputs, and verifies saved float projections. All tables, variability ranges, paired percentage decreases, figure ordinates, captions and integration wording now use Phi. The optional sum is retained only as the explicitly named sum_group_normalized_costs table column. The frozen protocol already specifies the maximum and remains unchanged.

No new training, timing, quality-evaluation or diagnostic campaign was run. No raw run file, witness, checkpoint, gate output or timing observation was edited. The superseded reporting artifacts are preserved in reporting_correction_20260926/superseded and are not current results. Raw preservation and unchanged timing checks are recorded in reporting_correction_verification.json.

## Corrected quality and effect on conclusions

Five-seed mean worst-group cost Phi for C0/C1/C2 is Adult 119.594 / 97.941 / 95.931, Bank 47.959 / 34.016 / 33.010, and Credit 18.303 / 13.461 / 12.973. The mean paired C0-to-C2 decreases are 19.8%, 31.2%, and 29.0%, respectively (previous sum-based values were 14.7%, 27.4%, and 25.3%). Updated SDs and seed ranges are in REPORT.md and tables/quality_summary.csv.

The quantitative quality values and improvement magnitudes change. The qualitative conclusions do not: refinement reduces the exact worst-group cost at every tested seed, all methods agree at matched budgets, Direct replay gains diminish with refinement, and both certificate variants fall back at round zero. All runtime ratios, wins/losses, raw timings and full indexed numerical-equality results are unchanged.
