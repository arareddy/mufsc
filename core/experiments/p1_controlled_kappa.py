"""P1: controlled-kappa theorem validation (Theorem thm:kappa, appendix
"Tight Heterogeneity Loss of the Natural Merged Summary").

Instantiates the exact two-client lower-bound construction for
kappa in {1,2,4,8,16,32,64,128} (eps = 1/(kappa+1)), runs Merged-1k, the
communication-matched Merged-2k, SplitGroup-2k, and a centralized quality
reference over >=10^4 seeds each, and compares:
  - the empirical E[G]/G*, E[Phi]/Phi* ratios against the analytical
    kappa/2, kappa/4 lower-bound order the paper proves;
  - Merged-1k's exact closed-form E[G] = (1+eps)/2 * L^2 for this specific
    construction (derived and hand-verified against a 4000-seed pilot
    before this sweep was written);
  - SplitGroup-2k's ratio staying flat (kappa-independent), the paper's
    central claim about why group-separated summaries are necessary.

Warm-start objectives only (no Fair-Lloyd refinement): "refinement can mask
an initialization failure and must not be the sole theorem-validation
metric" (appendix, Experiment 2).
"""
import csv
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from centralized import run_centralized  # noqa: E402
from merged_baseline import run_merged  # noqa: E402
from objective import fair_objective  # noqa: E402
from splitgroup import SplitGroupConfig, build_anchor_table, local_slice_step, server_step  # noqa: E402

KAPPAS = [1, 2, 4, 8, 16, 32, 64, 128]
N_SEEDS = 10_000
L = 10.0
UNIT = 150  # per-cell base count; base_n=(kappa+1)*UNIT is exactly divisible
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def make_construction(kappa: int, L: float, unit: int) -> tuple:
    eps = 1.0 / (kappa + 1)
    n_c1_A, n_c1_B = kappa * unit, unit          # (1-eps)*base_n, eps*base_n
    n_c2_A, n_c2_B = unit, kappa * unit          # eps*base_n, (1-eps)*base_n
    client_data = {
        0: np.concatenate([np.zeros((n_c1_A, 1)), np.full((n_c1_B, 1), L)]),
        1: np.concatenate([np.zeros((n_c2_A, 1)), np.zeros((n_c2_B, 1))]),
    }
    group_of = {
        0: np.concatenate([np.zeros(n_c1_A, dtype=np.int64), np.ones(n_c1_B, dtype=np.int64)]),
        1: np.concatenate([np.zeros(n_c2_A, dtype=np.int64), np.ones(n_c2_B, dtype=np.int64)]),
    }
    return client_data, group_of, eps


def pooled(client_data, group_of):
    keys = sorted(client_data)
    X = np.concatenate([client_data[c] for c in keys], axis=0)
    g = np.concatenate([group_of[c] for c in keys], axis=0)
    return X, g


def optimal_objectives(client_data, group_of, L):
    """Exact analytical minima for this driver's declared two-location witness."""
    from fractions import Fraction
    X,g=pooled(client_data,group_of)
    if X.shape[1]!=1 or not np.all((X==0)|(X==L)) or np.any(X[g==0]!=0):
        raise ValueError("analytical optimum only supports the declared P1 witness")
    e=Fraction(int(np.sum(X[g==1,0]==L)),int(np.sum(g==1)))
    distance=Fraction.from_float(float(L))
    return float(distance**2*e*(1-e/2)),float(distance**2*e*(1-e))


def run_splitgroup_warm(client_data, group_of, seed, k, gamma=0.0):
    cfg = SplitGroupConfig(k=k, gamma=gamma, num_groups=2)
    slice_results = {}
    for c, X_c in client_data.items():
        g_c = group_of[c]
        for g in (0, 1):
            mask = g_c == g
            if not np.any(mask):
                continue
            slice_results[(c, g)] = local_slice_step(X_c[mask], seed, c, g, cfg)
    n_A = int(sum(int(np.sum(group_of[c] == 0)) for c in client_data))
    n_B = int(sum(int(np.sum(group_of[c] == 1)) for c in client_data))
    anchor_table = build_anchor_table(slice_results, {0: n_A, 1: n_B}, cfg)
    return server_step(anchor_table, seed, cfg, anchor_lloyd_iters=0)


METHODS = {
    "merged_1k": lambda cd, go, seed, k: run_merged(cd, go, seed, k=k, k_reps=k),
    "merged_2k": lambda cd, go, seed, k: run_merged(cd, go, seed, k=k, k_reps=2 * k),
    "splitgroup_2k": lambda cd, go, seed, k: run_splitgroup_warm(cd, go, seed, k=k),
    "centralized": lambda cd, go, seed, k: run_centralized(cd, go, seed, k=k),
}


def alpha_k(k: int) -> float:
    return 5.0 * (math.log(k) + 2.0) if k > 1 else 10.0  # ln(1)=0, matches alpha_1=10


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    k = 1
    rows = []
    t0 = time.time()
    for kappa in KAPPAS:
        client_data, group_of, eps = make_construction(kappa, L, UNIT)
        X, g = pooled(client_data, group_of)
        G_star, Phi_star = optimal_objectives(client_data, group_of, L)

        for name, fn in METHODS.items():
            Gs, Phis, PhiAs, PhiBs = [], [], [], []
            for seed in range(N_SEEDS):
                centers = fn(client_data, group_of, seed, k)
                phi_a, phi_b, G, Phi = fair_objective(X, g, centers)
                Gs.append(G); Phis.append(Phi); PhiAs.append(phi_a); PhiBs.append(phi_b)
            Gs, Phis = np.array(Gs), np.array(Phis)
            row = dict(
                kappa=kappa, eps=eps, method=name, n_seeds=N_SEEDS,
                G_star=G_star, Phi_star=Phi_star,
                mean_G=Gs.mean(), se_G=Gs.std(ddof=1) / math.sqrt(N_SEEDS),
                mean_Phi=Phis.mean(), se_Phi=Phis.std(ddof=1) / math.sqrt(N_SEEDS),
                ratio_G=Gs.mean() / G_star, ratio_Phi=Phis.mean() / Phi_star,
                mean_Phi_A=np.mean(PhiAs), mean_Phi_B=np.mean(PhiBs),
            )
            rows.append(row)
            print(f"kappa={kappa:4d} eps={eps:.4f} method={name:14s} "
                  f"E[G]/G*={row['ratio_G']:8.3f}  E[Phi]/Phi*={row['ratio_Phi']:8.3f}  "
                  f"(elapsed {time.time()-t0:.1f}s)", flush=True)

    csv_path = os.path.join(RESULTS_DIR, "p1_controlled_kappa.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {csv_path}")
    return rows


if __name__ == "__main__":
    raise SystemExit("Reference helper driver only. Execute corrected gated runs with: python remediation/scripts/run_experiments.py --stages P1 --run-id corrected-v1")
