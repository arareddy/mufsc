"""Train(X; s): the declared federated fair k-means training map.

Phase I (SplitGroup-2k) produces the warm-start centers and the checkpoint
state unlearning needs to recompute touched slices exactly. Phase II
(exact (N,S,SS) aggregation + GFU_L) refines them for T rounds. The
returned checkpoint carries everything the appendix's "training checkpoint"
paragraph requires: per-slice anchors/multiplicities, group sizes, the
indexed center trajectory with exact per-round aggregates, and per-client
per-point cached label/d1/d2/runner-up at every round.
"""
import numpy as np
from time import perf_counter
from validation import training_inputs

from assignment import assign_all
from digest import round_digest
from fair_update import guarded_fair_update
from fixedpoint import (FixedPointConfig, accumulate_stats, add_stats,
                         dequantize, new_zero_stats, quantize, represented_clients)
from splitgroup import SplitGroupConfig, build_anchor_table, local_slice_step, server_step
from timing import add_to, new_timing

DEFAULT_FP_CFG = FixedPointConfig(scale_bits=16, clip=8.0)


def train_full(client_data: dict, group_of: dict, seed: int, k: int, T: int, L: int,
               gamma: float = 0.0, fp_cfg: FixedPointConfig = None,
               anchor_lloyd_iters: int = 0, build_cache: bool = True) -> dict:
    """
    client_data: {client_id: X_client (n_c, d) float64, already standardized
                  and featurized -- this function does not fit preprocessing}
    group_of:    {client_id: group_array (n_c,) int in {0, 1}}
    """
    fp_cfg = fp_cfg or DEFAULT_FP_CFG
    training_inputs(client_data, group_of, seed, k, T, L, gamma, fp_cfg, anchor_lloyd_iters)
    encoding_start = perf_counter()
    client_data, encoded_data = represented_clients(client_data, fp_cfg)
    encoding_seconds = perf_counter() - encoding_start
    group_of = {c: np.asarray(group_of[c], dtype=np.int64).copy() for c in sorted(client_data)}
    d = next(iter(client_data.values())).shape[1]
    sg_cfg = SplitGroupConfig(k=k, gamma=gamma, num_groups=2)
    timing = new_timing(client_data.keys(), T)

    timing["encoding"] = encoding_seconds
    slice_results = {}
    for c, X_c in client_data.items():
        g_c = group_of[c]
        for g in (0, 1):
            mask = g_c == g
            if not np.any(mask):
                continue
            with add_to(timing["phase1_client"], c):
                slice_results[(c, g)] = local_slice_step(X_c[mask], seed, c, g, sg_cfg)

    n_A = int(sum(int(np.sum(group_of[c] == 0)) for c in client_data))
    n_B = int(sum(int(np.sum(group_of[c] == 1)) for c in client_data))
    group_sizes = {0: n_A, 1: n_B}

    with add_to(timing, "phase1_server"):
        anchor_table = build_anchor_table(slice_results, group_sizes, sg_cfg)
        centers = server_step(anchor_table, seed, sg_cfg, anchor_lloyd_iters)

    trajectory = [centers.copy()]
    per_round_stats = []
    digests = []
    client_cache = {c: {} for c in client_data}

    for t in range(T):
        N, S, SS = new_zero_stats(2, k, d)
        for c, X_c in client_data.items():
            with add_to(timing["phase2_client_recompute"][c], t):
                g_c = group_of[c].astype(np.int64)
                X_int = encoded_data[c]
                X_float = X_c
                labels, d1, d2, runner_up = assign_all(X_float, centers)
                N_c, S_c, SS_c = accumulate_stats(X_int, g_c, labels, 2, k)
            with add_to(timing, "phase2_server"):
                N, S, SS = add_stats((N, S, SS), (N_c, S_c, SS_c))
            if build_cache:
                with add_to(timing, "cache_construction"):
                    client_cache[c][t] = {"labels": labels, "d1": d1, "d2": d2, "runner_up": runner_up}

        per_round_stats.append((N, S, SS))
        digests.append(round_digest(centers, N, S, SS))

        with add_to(timing, "phase2_server"):
            centers, info = guarded_fair_update(centers, N, S, SS, n_A, n_B, k, L, fp_cfg.scale)
        trajectory.append(centers.copy())

    return {
        "map_version": "FTF-1", "cache_valid": bool(build_cache),
        "encoded_data": encoded_data,
        "seed": seed, "k": k, "T": T, "L": L, "gamma": gamma,
        "fp_cfg": fp_cfg, "anchor_lloyd_iters": anchor_lloyd_iters,
        "client_ids": sorted(client_data.keys()),
        "client_data": client_data,
        "group_of": group_of,
        "group_sizes": group_sizes,
        "slice_results": slice_results,
        "anchor_table": anchor_table,
        "trajectory": trajectory,
        "per_round_stats": per_round_stats,
        "digests": digests,
        "client_cache": client_cache,
        "final_centers": centers,
        "timing": timing,
    }
