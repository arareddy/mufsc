"""Merged-Nk: the natural one-summary-per-client baseline Theorem thm:kappa
is stated against.

Each physical client runs ONE weighted k-means++ instance on its pooled
(both-groups) local data, weighted by the client's OWN per-group count
1/n_{c,g(x)} -- "locally group-balanced" -- and sends up to N*k
representatives. Each representative's server-side weight uses the GLOBAL
group sizes (h_A/n_A + h_B/n_B), which is what the social-fairness
objective actually normalizes by. The mismatch between the local balance
used to *choose* representatives and the global balance the objective
needs is exactly the mechanism Theorem thm:kappa proves costs a
Theta(kappa) factor whenever a client's local group mix diverges from the
population's -- SplitGroup-2k avoids it by never mixing groups within one
seeding call in the first place.

N=1 (k_reps=k) is Merged-1k; N=2 (k_reps=2k) is the communication-matched
Merged-2k baseline the experiment plan also calls for.

Representatives are snapped to the same coarse communication grid
SplitGroup-2k uses (splitgroup.snap_gamma) before being sent -- the
kappa-upper-bound proof for this baseline (app:kappa-proof) explicitly
carries a Q <= d*gamma**2/2 quantization term for it too, so gamma=0
(the previous, quantization-free version of this module) was only ever
the gamma=0 point of a sweep, not the only way this baseline is defined.
"""
import numpy as np
from fractions import Fraction

from assignment import assign_labels_only
from kmeanspp import weighted_kmeanspp
from rng import canonical_tape
from splitgroup import snap_gamma


def merged_slice_step(X_c: np.ndarray, group_c: np.ndarray, seed: int, client_id: int,
                       k_reps: int, gamma: float = 0.0) -> dict:
    n_cA = int(np.sum(group_c == 0))
    n_cB = int(np.sum(group_c == 1))
    w_local = [Fraction(1, n_cA if int(g)==0 else n_cB) for g in group_c]
    tape = canonical_tape(seed, "merged_local", client_id)
    k_e = min(k_reps, X_c.shape[0])
    selected_idx = weighted_kmeanspp(X_c, w_local, k_e, tape)
    reps = X_c[selected_idx]
    labels = assign_labels_only(X_c, reps)
    h_A = np.array([int(np.sum((labels == j) & (group_c == 0))) for j in range(k_e)])
    h_B = np.array([int(np.sum((labels == j) & (group_c == 1))) for j in range(k_e)])
    anchors = snap_gamma(reps, gamma)
    return {"anchors": anchors, "reps": reps, "h_A": h_A, "h_B": h_B, "k_e": k_e, "selected_idx": selected_idx}


def build_merged_anchor_table(slice_results: dict, n_A: int, n_B: int) -> dict:
    keys = sorted(slice_results.keys())  # canonical order: ascending client id
    anchors, weights = [], []
    for c in keys:
        res = slice_results[c]
        for j in range(res["k_e"]):
            anchors.append(res["anchors"][j])
            w = Fraction(int(res["h_A"][j]), n_A) + Fraction(int(res["h_B"][j]), n_B)
            weights.append(w)
    return {"anchors": np.array(anchors, dtype=np.float64) if anchors else np.zeros((0, 0)),
            "weights": np.array(weights, dtype=object)}


def merged_server_step(anchor_table: dict, seed: int, k: int) -> np.ndarray:
    tape = canonical_tape(seed, "merged_server")
    idx = weighted_kmeanspp(anchor_table["anchors"], anchor_table["weights"], k, tape)
    return anchor_table["anchors"][idx].copy()


def run_merged(client_data: dict, group_of: dict, seed: int, k: int, k_reps: int,
               gamma: float = 0.0, return_slices: bool = False):
    """Merged-(k_reps)k Phase-I warm start. k_reps=k is Merged-1k;
    k_reps=2*k is the communication-matched Merged-2k baseline. gamma=0
    (the default) leaves represented anchors unsnapped. FTF-1 seeding
    changes the old finite-CDF seed-to-output map."""
    n_A = int(sum(int(np.sum(group_of[c] == 0)) for c in client_data))
    n_B = int(sum(int(np.sum(group_of[c] == 1)) for c in client_data))
    slice_results = {c: merged_slice_step(client_data[c], group_of[c], seed, c, k_reps, gamma)
                      for c in sorted(client_data) if len(client_data[c])}
    anchor_table = build_merged_anchor_table(slice_results, n_A, n_B)
    centers = merged_server_step(anchor_table, seed, k)
    if return_slices:
        return centers, slice_results
    return centers
