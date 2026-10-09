"""Unlearn(checkpoint, R; s): exact batch replay (Algorithm 1 of the paper).

Phase I: every pseudo-client (c,g) untouched by R reuses its cached
(anchors, multiplicities) verbatim; every touched slice is rerun on its
reduced data with the identical tape (seed, "local", c, g) fresh training
would use. The server is always rerun -- deleting any group-g record
changes every h/n_g weight for that group.

Phase II: one replay loop serves fresh-training-equivalent "direct full
replay" (certificate_mode="none") and both certified variants
(certificate_mode="basic" | "runnerup") -- direct replay is exactly
certified replay with the certificate short-circuit disabled, not a
separate implementation, so a speed claim for certification can never be
an artifact of two differently-optimized code paths.

At each round: cached labels/d1/d2/runner-up for retained survivors come
from the checkpoint's per-point cache; removed points' cached contribution
(at that round's cached label) is subtracted; certified survivors need no
further change; every other survivor (uncertified, or every survivor once
abandonment has fired) is directly reassigned against the true replay
centers, with its cached contribution replaced by its true one. The same
deterministic GFU_L map is then applied, exactly as fresh training would.

Abandonment threshold is left as an explicit, documented parameter: the
specification requires an abandonment criterion (Algorithm 1, line 12) but
never defines one numerically anywhere in the paper. 0.5 (a majority of
tracked survivors failing certification) is this implementation's declared
choice, not a value derived from the theory.
"""
import numpy as np
from time import perf_counter
from exact_numeric import norm_bounds
from validation import removal_request

from assignment import assign_all
from certificates import basic_certificate_vec, runner_up_certificate_vec
from digest import round_digest
from fair_update import guarded_fair_update
from fixedpoint import accumulate_stats, add_stats, dequantize, new_zero_stats, quantize, sub_stats
from splitgroup import SplitGroupConfig, build_anchor_table, local_slice_step, server_step
from timing import add_to, new_timing

DEFAULT_ABANDON_THRESHOLD = 0.5


def _center_shift(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return norm_bounds(a, b)


def _phase1_rewind_or_skip(checkpoint: dict, removed: dict, timing: dict) -> tuple:
    """Returns (new_slice_results, new_group_sizes) for the retained data."""
    sg_cfg = _sg_cfg_from_checkpoint(checkpoint)
    group_of = checkpoint["group_of"]
    client_data = checkpoint["client_data"]
    seed = checkpoint["seed"]

    new_slice_results = {}
    for (c, g), cached in checkpoint["slice_results"].items():
        with add_to(timing["phase1_client"], c):
            removed_c = removed.get(c, np.array([], dtype=np.int64))
            g_c = group_of[c]
            slice_mask = g_c == g
            touched = np.any(np.isin(removed_c, np.where(slice_mask)[0]))
            if not touched:
                new_slice_results[(c, g)] = cached
                continue
            retained_slice_mask = slice_mask.copy()
            retained_slice_mask[removed_c] = False
            X_slice = client_data[c][retained_slice_mask]
            if X_slice.shape[0] == 0:
                continue  # slice emptied by the deletion: dropped, per the declared map
            new_slice_results[(c, g)] = local_slice_step(X_slice, seed, c, g, sg_cfg)

    n_A = 0
    n_B = 0
    for c, X_c in client_data.items():
        g_c = group_of[c]
        removed_c = removed.get(c, np.array([], dtype=np.int64))
        retained_mask = np.ones(X_c.shape[0], dtype=bool)
        retained_mask[removed_c] = False
        n_A += int(np.sum((g_c == 0) & retained_mask))
        n_B += int(np.sum((g_c == 1) & retained_mask))

    if n_A == 0 or n_B == 0:
        raise ValueError("invalid removal request: empties a declared global group")

    return new_slice_results, {0: n_A, 1: n_B}


def _sg_cfg_from_checkpoint(checkpoint: dict):
    return SplitGroupConfig(k=checkpoint["k"], gamma=checkpoint["gamma"], num_groups=2)


def _retained_views(checkpoint: dict, removed: dict) -> dict:
    client_data = checkpoint["client_data"]
    group_of = checkpoint["group_of"]
    fp_cfg = checkpoint["fp_cfg"]
    views = {}
    for c, X_c in client_data.items():
        removed_c = removed.get(c, np.array([], dtype=np.int64))
        retained_mask = np.ones(X_c.shape[0], dtype=bool)
        retained_mask[removed_c] = False
        removed_mask = ~retained_mask
        X_retained_int = checkpoint["encoded_data"][c][retained_mask]
        views[c] = {
            "retained_mask": retained_mask,
            "removed_mask": removed_mask,
            # Assignment must run on the same dequantize(quantize(.)) view
            # train.py uses (Phase II operates on the exact grid throughout,
            # not on the pre-quantization floats), or a failing point's
            # recomputed label could differ from what fresh training would
            # have assigned it, breaking bit-for-bit trajectory equality.
            "X_retained": dequantize(X_retained_int, fp_cfg),
            "X_retained_int": X_retained_int,
            "group_retained": group_of[c][retained_mask].astype(np.int64),
            "X_removed_int": checkpoint["encoded_data"][c][removed_mask],
            "group_removed": group_of[c][removed_mask].astype(np.int64),
        }
    return views


def _certify(labels, d1, d2, runner_up, delta, k, mode):
    if k == 1:
        return np.ones_like(labels, dtype=bool)  # no assignment ambiguity possible
    if mode == "basic":
        return basic_certificate_vec(d1, d2, labels, delta)
    if mode == "runnerup":
        return runner_up_certificate_vec(d1, d2, labels, runner_up, delta)
    raise ValueError(f"unknown certificate mode {mode!r}")


def _replay_phase2(checkpoint: dict, views: dict, C0_prime: np.ndarray,
                    n_A: int, n_B: int, certificate_mode: str,
                    abandon_threshold: float, timing: dict) -> dict:
    k, T, L, d = checkpoint["k"], checkpoint["T"], checkpoint["L"], C0_prime.shape[1]
    client_ids = checkpoint["client_ids"]
    cached_trajectory = checkpoint["trajectory"]
    cached_stats = checkpoint["per_round_stats"]
    client_cache = checkpoint["client_cache"]

    centers = C0_prime
    trajectory = [centers.copy()]
    digests = []
    diagnostics = []
    per_round_stats = []
    abandoned = certificate_mode == "none"
    abandonment_round = 0 if abandoned else None

    for t in range(T):
        round_start = perf_counter()
        with add_to(timing, "shift_bounds"):
            delta = _center_shift(centers, cached_trajectory[t])
        N_cached, S_cached, SS_cached = cached_stats[t]

        if not abandoned:
            total_survivors, total_failing = 0, 0
            N, S, SS = N_cached, S_cached, SS_cached
            for c in client_ids:
                v = views[c]
                rm, om = v["retained_mask"], v["removed_mask"]
                cache_t = client_cache[c][t]

                # Each client computes its OWN exact delta locally (its
                # removed points' old contribution, and any of its own
                # failing points' old/new contribution) -- that is real
                # client-side compute. Folding a client's delta into the
                # shared running (N,S,SS) is what the server does once it
                # receives every client's delta, so it is timed separately
                # below as phase2_server, mirroring train.py's own split.
                removed_stats = None
                with add_to(timing["phase2_client_recompute"][c], t):
                    if om.any():
                        old_labels = cache_t["labels"][om]
                        removed_stats = accumulate_stats(
                            v["X_removed_int"], v["group_removed"], old_labels, 2, k)

                labels_r = cache_t["labels"][rm]
                d1_r, d2_r, ru_r = cache_t["d1"][rm], cache_t["d2"][rm], cache_t["runner_up"][rm]
                scan_start = perf_counter()
                with add_to(timing["phase2_client_certify"][c], t):
                    passed = _certify(labels_r, d1_r, d2_r, ru_r, delta, k, certificate_mode)
                timing["certificate_scan"] += perf_counter() - scan_start
                failing = ~passed
                total_survivors += rm.sum()
                total_failing += int(failing.sum())

                fail_old_stats = fail_new_stats = None
                if failing.any():
                    fail_start = perf_counter()
                    with add_to(timing["phase2_client_recompute"][c], t):
                        X_fail_int = v["X_retained_int"][failing]
                        X_fail_float = v["X_retained"][failing]
                        group_fail = v["group_retained"][failing]
                        new_labels = assign_all(X_fail_float, centers)[0]
                        fail_old_stats = accumulate_stats(X_fail_int, group_fail, labels_r[failing], 2, k)
                        fail_new_stats = accumulate_stats(X_fail_int, group_fail, new_labels, 2, k)
                    timing["failed_assignment"] += perf_counter() - fail_start

                with add_to(timing, "phase2_server"):
                    if removed_stats is not None:
                        N, S, SS = sub_stats((N, S, SS), removed_stats)
                    if fail_old_stats is not None:
                        N, S, SS = sub_stats((N, S, SS), fail_old_stats)
                        N, S, SS = add_stats((N, S, SS), fail_new_stats)

            frac_failing = total_failing / total_survivors if total_survivors else 0.0
            diagnostics.append({"round": t, "certified": int(total_survivors - total_failing),
                                 "failing": total_failing, "abandoned_this_round": False,
                                 "N": int(total_survivors), "A": int(total_survivors),
                                 "P": int(total_survivors-total_failing), "S": int(total_survivors-total_failing), "J": 0})
            threshold_num, threshold_den = float(abandon_threshold).as_integer_ratio()
            if total_failing * threshold_den > threshold_num * total_survivors:
                abandoned = True
                abandonment_round = t
                timing["fallback_sunk"] += perf_counter() - round_start
                with add_to(timing, "fallback_rebuild"):
                    N, S, SS = _direct_rebuild(views, client_ids, centers, k, d, timing, t)
                diagnostics[-1]["S"] = 0
                diagnostics[-1]["J"] = total_failing
                diagnostics[-1]["abandoned_this_round"] = True
        else:
            N, S, SS = _direct_rebuild(views, client_ids, centers, k, d, timing, t)
            diagnostics.append({"round": t, "certified": 0, "failing": 0, "abandoned_this_round": True,
                                "N": sum(len(v["X_retained"]) for v in views.values()), "A": 0, "P": 0, "S": 0, "J": 0})

        per_round_stats.append((N, S, SS))
        digests.append(round_digest(centers, N, S, SS))
        with add_to(timing, "phase2_server"):
            centers, _ = guarded_fair_update(centers, N, S, SS, n_A, n_B, k, L, checkpoint["fp_cfg"].scale)
        trajectory.append(centers.copy())

    return {
        "map_version": "FTF-1", "cache_valid": False, "per_round_stats": per_round_stats,
        "trajectory": trajectory,
        "digests": digests,
        "final_centers": centers,
        "diagnostics": diagnostics,
        "abandonment_round": abandonment_round,
    }


def _direct_rebuild(views: dict, client_ids: list, centers: np.ndarray, k: int, d: int,
                     timing: dict, t: int) -> tuple:
    N, S, SS = new_zero_stats(2, k, d)
    for c in client_ids:
        v = views[c]
        if v["X_retained"].shape[0] == 0:
            continue
        with add_to(timing["phase2_client_recompute"][c], t):
            labels = assign_all(v["X_retained"], centers)[0] if k > 1 else \
                np.zeros(v["X_retained"].shape[0], dtype=np.int64)
            N_c, S_c, SS_c = accumulate_stats(v["X_retained_int"], v["group_retained"], labels, 2, k)
        with add_to(timing, "phase2_server"):
            N, S, SS = add_stats((N, S, SS), (N_c, S_c, SS_c))
    return N, S, SS


def unlearn(checkpoint: dict, removed: dict, certificate_mode: str = "runnerup",
            abandon_threshold: float = DEFAULT_ABANDON_THRESHOLD) -> dict:
    """
    removed: {client_id: np.ndarray of local row indices to delete}.
    certificate_mode: "none" (direct full replay baseline), "basic", or "runnerup".
    """
    removed = removal_request(checkpoint, removed, certificate_mode, abandon_threshold)
    timing = new_timing(checkpoint["client_ids"], checkpoint["T"])
    new_slice_results, new_group_sizes = _phase1_rewind_or_skip(checkpoint, removed, timing)
    sg_cfg = _sg_cfg_from_checkpoint(checkpoint)
    with add_to(timing, "phase1_server"):
        anchor_table = build_anchor_table(new_slice_results, new_group_sizes, sg_cfg)
        C0_prime = server_step(anchor_table, checkpoint["seed"], sg_cfg, checkpoint["anchor_lloyd_iters"])

    with add_to(timing, "input_materialization"):
        views = _retained_views(checkpoint, removed)
    result = _replay_phase2(checkpoint, views, C0_prime, new_group_sizes[0], new_group_sizes[1],
                             certificate_mode, abandon_threshold, timing)
    result["slice_results"] = new_slice_results
    result["group_sizes"] = new_group_sizes
    result["anchor_table"] = anchor_table
    result["timing"] = timing
    return result
