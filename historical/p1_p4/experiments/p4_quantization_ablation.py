"""P4: quantization and initialization ablation (EXPERIMENT_EXECUTION_PLAN.md
P4 / appendix Experiment 3).

Compares Merged-1k, SplitGroup-2k, communication-matched Merged-2k, and a
centralized weighted k-means++ reference, sweeping gamma over >=5 values
(0.0, 0.01, 0.05, 0.1, 0.5, 1.0 -- 0.0 IS "SplitGroup-2k with no
quantization", the fifth listed comparison point, not a separate method).
Logs quantization error, anchor collisions, local/warm-start/final
objectives, communication (anchor scalars sent), and server time, on the
same real Adult/Bank/Credit federations P2 uses (one fixed, moderate k per
dataset rather than P2's full k-grid -- this experiment isolates the
gamma/method effect, holding k fixed, not sweeping k too).

Centralized has no representative/anchor step at all, so gamma does not
apply to it -- computed once per dataset as a gamma-independent reference
line, not swept.
"""
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from assignment import assign_all  # noqa: E402
from centralized import run_centralized  # noqa: E402
from datasets import load_dataset  # noqa: E402
from fair_update import guarded_fair_update  # noqa: E402
from fixedpoint import FixedPointConfig, accumulate_stats, add_stats, dequantize, new_zero_stats, quantize  # noqa: E402
from merged_baseline import merged_server_step, merged_slice_step, build_merged_anchor_table  # noqa: E402
from objective import fair_objective  # noqa: E402
from splitgroup import SplitGroupConfig, build_anchor_table, local_slice_step, server_step  # noqa: E402

GAMMAS = [0.0, 0.01, 0.05, 0.1, 0.5, 1.0]
K_BY_DATASET = {"adult": 8, "bank": 8, "credit": 8}
T_ROUNDS = 15
L_BISECTION = 6
SCALE_BITS = 12
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def quantization_stats(slice_results: dict) -> dict:
    """Mean/max ||q-z||^2 and anchor-collision count, pooled across every
    slice/client's representatives (empty for gamma=0: q==z exactly)."""
    errs, anchors = [], []
    for res in slice_results.values():
        diff = res["anchors"] - res["reps"]
        errs.append(np.sum(diff ** 2, axis=1))
        anchors.append(res["anchors"])
    errs = np.concatenate(errs) if errs else np.array([0.0])
    anchors = np.concatenate(anchors, axis=0) if anchors else np.zeros((0, 1))
    n_total = anchors.shape[0]
    n_unique = len(np.unique(np.round(anchors, 10), axis=0)) if n_total else 0
    return dict(mean_quant_err=float(errs.mean()), max_quant_err=float(errs.max()),
                n_anchors=n_total, n_collisions=n_total - n_unique)


def run_phase2_from_centers(client_data: dict, group_of: dict, centers0: np.ndarray,
                             seed: int, k: int, T: int, L: int, fp_cfg: FixedPointConfig) -> np.ndarray:
    """Continues the declared Phase-II refinement from an externally
    supplied warm start -- lets any Phase-I method's output be scored
    "after refinement" through the identical GuardedFairUpdate loop
    train_full uses, without coupling this ablation's baselines into
    train.py's own declared-map signature."""
    d = centers0.shape[1]
    n_A = int(sum(int(np.sum(group_of[c] == 0)) for c in client_data))
    n_B = int(sum(int(np.sum(group_of[c] == 1)) for c in client_data))
    centers = centers0.copy()
    for _ in range(T):
        N, S, SS = new_zero_stats(2, k, d)
        for c, X_c in client_data.items():
            g_c = group_of[c].astype(np.int64)
            X_int = quantize(X_c, fp_cfg)
            X_float = dequantize(X_int, fp_cfg)
            labels = assign_all(X_float, centers)[0]
            N_c, S_c, SS_c = accumulate_stats(X_int, g_c, labels, 2, k)
            N, S, SS = add_stats((N, S, SS), (N_c, S_c, SS_c))
        centers, _ = guarded_fair_update(centers, N, S, SS, n_A, n_B, k, L, fp_cfg.scale)
    return centers


def run_splitgroup(client_data, group_of, seed, k, gamma, fp_cfg):
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
    t0 = time.perf_counter()
    centers = server_step(anchor_table, seed, cfg, anchor_lloyd_iters=0)
    server_time = time.perf_counter() - t0
    n_scalars = sum(r["k_e"] * r["anchors"].shape[1] for r in slice_results.values())
    return centers, quantization_stats(slice_results), server_time, n_scalars


def run_merged_variant(client_data, group_of, seed, k, k_reps, gamma):
    n_A = int(sum(int(np.sum(group_of[c] == 0)) for c in client_data))
    n_B = int(sum(int(np.sum(group_of[c] == 1)) for c in client_data))
    slice_results = {c: merged_slice_step(client_data[c], group_of[c], seed, c, k_reps, gamma)
                      for c in client_data}
    anchor_table = build_merged_anchor_table(slice_results, n_A, n_B)
    t0 = time.perf_counter()
    centers = merged_server_step(anchor_table, seed, k)
    server_time = time.perf_counter() - t0
    n_scalars = sum(r["k_e"] * r["anchors"].shape[1] for r in slice_results.values())
    return centers, quantization_stats(slice_results), server_time, n_scalars


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = []
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "v0", "data")

    for name in ("adult", "bank", "credit"):
        client_data, group_of, meta = load_dataset(name, data_dir, seed=0)
        fp_cfg = FixedPointConfig(scale_bits=SCALE_BITS, clip=meta["clip"])
        k = K_BY_DATASET[name]
        X_all = np.concatenate([client_data[c] for c in sorted(client_data)], axis=0)
        g_all = np.concatenate([group_of[c] for c in sorted(group_of)], axis=0)
        seed = 42
        print(f"[{name}] C={meta['num_clients']} n={meta['n_total']} d={meta['d']} k={k}", flush=True)

        # Centralized: gamma-independent reference, computed once.
        t0 = time.perf_counter()
        cent_centers = run_centralized(client_data, group_of, seed, k)
        cent_server_time = time.perf_counter() - t0
        pa, pb, G, Phi = fair_objective(X_all, g_all, cent_centers)
        cent_final = run_phase2_from_centers(client_data, group_of, cent_centers, seed, k,
                                              T_ROUNDS, L_BISECTION, fp_cfg)
        pa_f, pb_f, G_f, Phi_f = fair_objective(X_all, g_all, cent_final)
        rows.append(dict(dataset=name, k=k, gamma="", method="centralized",
                          mean_quant_err="", max_quant_err="", n_anchors="", n_collisions="",
                          n_scalars_sent=k * meta["d"], server_seconds=cent_server_time,
                          warm_G=G, warm_Phi=Phi, warm_Phi_A=pa, warm_Phi_B=pb,
                          final_G=G_f, final_Phi=Phi_f, final_Phi_A=pa_f, final_Phi_B=pb_f))

        for gamma in GAMMAS:
            for method, runner in (
                ("merged_1k", lambda: run_merged_variant(client_data, group_of, seed, k, k, gamma)),
                ("merged_2k", lambda: run_merged_variant(client_data, group_of, seed, k, 2 * k, gamma)),
                ("splitgroup_2k", lambda: run_splitgroup(client_data, group_of, seed, k, gamma, fp_cfg)),
            ):
                centers, qstats, server_time, n_scalars = runner()
                pa, pb, G, Phi = fair_objective(X_all, g_all, centers)
                final_centers = run_phase2_from_centers(client_data, group_of, centers, seed, k,
                                                         T_ROUNDS, L_BISECTION, fp_cfg)
                pa_f, pb_f, G_f, Phi_f = fair_objective(X_all, g_all, final_centers)
                rows.append(dict(dataset=name, k=k, gamma=gamma, method=method,
                                  mean_quant_err=qstats["mean_quant_err"], max_quant_err=qstats["max_quant_err"],
                                  n_anchors=qstats["n_anchors"], n_collisions=qstats["n_collisions"],
                                  n_scalars_sent=n_scalars, server_seconds=server_time,
                                  warm_G=G, warm_Phi=Phi, warm_Phi_A=pa, warm_Phi_B=pb,
                                  final_G=G_f, final_Phi=Phi_f, final_Phi_A=pa_f, final_Phi_B=pb_f))
                print(f"  gamma={gamma:5.2f} {method:14s} warm_Phi={Phi:8.4f} final_Phi={Phi_f:8.4f} "
                      f"collisions={qstats['n_collisions']}/{qstats['n_anchors']} "
                      f"server_s={server_time:.4f}", flush=True)

        out_path = os.path.join(RESULTS_DIR, "p4_quantization_ablation.csv")
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    print(f"\nDONE. {len(rows)} rows written to {out_path}")


if __name__ == "__main__":
    raise SystemExit("Reference helper driver only. Execute corrected gated runs with: python remediation/scripts/run_experiments.py --stages P4 --run-id corrected-v1")
