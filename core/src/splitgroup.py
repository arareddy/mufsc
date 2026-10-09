"""Phase I: SplitGroup-2k.

Each physical client c is split into per-group pseudo-clients (c,g). Each
nonempty slice runs *ordinary* (unweighted) seeding-only k-means++ with its
own keyed tape, assigns its own records to the nearest selected
representative to get exact multiplicities, and quantizes each
representative onto a coarse communication grid (snap_gamma) -- distinct
from the fine fixed-point grid used for exact (N,S,SS) accumulation
elsewhere. Both phases consume the same represented fine-grid X. Gamma
changes anchor locations; float64 coordinate payload size is unchanged.

The server never sees raw points or a dense reconstruction of them: it
receives a canonical (c,g,j)-ordered anchor list with weights h/n_g and
runs weighted k-means++ (kmeanspp.weighted_kmeanspp) directly on that list.
"Dense synthetic expansion is not part of the method" (paper, Fig. 1
caption) -- this module never regenerates points from anchors.
"""
from dataclasses import dataclass

import numpy as np
from fractions import Fraction
from exact_numeric import rational, squared_exact, finite_matrix

from assignment import assign_labels_only
from kmeanspp import ordinary_kmeanspp, weighted_kmeanspp
from rng import canonical_tape


@dataclass(frozen=True)
class SplitGroupConfig:
    k: int
    gamma: float  # anchor communication grid; gamma=0 disables snapping
    num_groups: int = 2


def snap_gamma(Z: np.ndarray, gamma: float) -> np.ndarray:
    """Deterministic grid quantization of representatives for communication.

    gamma=0 means "no quantization" (send exact float64 representatives);
    this is a legitimate ablation point in the paper's own experiment plan,
    not a degenerate case to special-case away.
    """
    Z = finite_matrix(Z, "representatives")
    if not np.isfinite(gamma) or gamma < 0:
        raise ValueError("gamma must be finite and nonnegative")
    if gamma == 0: return Z.copy()
    step = rational(gamma)
    out = np.array([float(round(rational(x) / step) * step) for x in Z.flat]).reshape(Z.shape)
    return finite_matrix(out, "snapped anchors")


def local_slice_step(X_slice: np.ndarray, seed: int, client_id: int, group_id: int,
                      cfg: SplitGroupConfig) -> dict:
    """One pseudo-client's Phase-I contribution: anchors and multiplicities.

    Returns a dict with 'anchors' (k_e, d) quantized representatives,
    'mult' (k_e,) multiplicities, and 'selected_idx' (k_e,) the local row
    indices chosen as representatives (needed by unlearning to test whether
    a deletion touches a previously selected representative).
    """
    if cfg.k < 1 or cfg.num_groups != 2:
        raise ValueError("positive k and binary groups required")
    X_slice = finite_matrix(X_slice, "slice")
    n_e = X_slice.shape[0]
    if n_e == 0: raise ValueError("empty local slice must be omitted")
    k_e = min(cfg.k, n_e)
    tape = canonical_tape(seed, "local", client_id, group_id)
    selected_idx = ordinary_kmeanspp(X_slice, k_e, tape)
    reps = X_slice[selected_idx]

    labels = assign_labels_only(X_slice, reps)
    mult = np.bincount(labels, minlength=k_e).astype(np.int64)

    anchors = snap_gamma(reps, cfg.gamma)
    return {
        "anchors": anchors,
        "reps": reps,  # pre-quantization representatives, for measuring quantization error
        "mult": mult,
        "selected_idx": selected_idx,
        "k_e": k_e,
        "n_e": n_e,
    }


def build_anchor_table(slice_results: dict, group_sizes: dict, cfg: SplitGroupConfig) -> dict:
    """Canonical (c,g,j)-ordered anchor list with weights h/n_g.

    slice_results: {(c,g): local_slice_step(...) output}, only nonempty
    slices present. group_sizes: {g: n_g}, g in range(cfg.num_groups).
    """
    keys = sorted(slice_results.keys())  # canonical order: ascending (c,g)
    anchors, weights, owner = [], [], []
    for (c, g) in keys:
        res = slice_results[(c, g)]
        n_g = group_sizes[g]
        for j in range(res["k_e"]):
            anchors.append(res["anchors"][j])
            weights.append(Fraction(int(res["mult"][j]), int(n_g)))
            owner.append((c, g, j))
    return {
        "anchors": np.array(anchors, dtype=np.float64) if anchors else np.zeros((0, 0)),
        "weights": np.array(weights, dtype=object),
        "owner": owner,
    }


def server_step(anchor_table: dict, seed: int, cfg: SplitGroupConfig,
                 anchor_lloyd_iters: int = 0) -> np.ndarray:
    """Weighted k-means++ on the compact anchor set, plus optional weighted
    anchor-Lloyd rounds that are required (by the declared map) to never
    increase the weighted anchor objective -- checked, not assumed.
    """
    anchors = anchor_table["anchors"]
    weights = anchor_table["weights"]
    tape = canonical_tape(seed, "server")
    idx = weighted_kmeanspp(anchors, weights, cfg.k, tape)
    centers = anchors[idx].copy()

    for _ in range(anchor_lloyd_iters):
        labels = assign_labels_only(anchors, centers)
        candidate = _weighted_lloyd_update(anchors, weights, labels, centers, cfg.k)
        if _weighted_objective(anchors, weights, candidate) <= _weighted_objective(anchors, weights, centers):
            centers = candidate
        else:
            break  # guard: never accept a non-improving anchor-Lloyd step

    return centers


def _weighted_lloyd_update(anchors: np.ndarray, weights: np.ndarray, labels: np.ndarray,
                            old_centers: np.ndarray, k: int) -> np.ndarray:
    new_centers = old_centers.copy()
    for j in range(k):
        mask = labels == j
        w = weights[mask]
        if w.sum() > 0:
            den = sum(rational(v) for v in w)
            new_centers[j] = [float(sum(rational(v)*rational(x) for v,x in zip(w,anchors[mask, q]))/den)
                              for q in range(anchors.shape[1])]
        # empty cell: canonical rule retains the old indexed center
    return new_centers


def _weighted_objective(anchors: np.ndarray, weights: np.ndarray, centers: np.ndarray) -> float:
    labels = assign_labels_only(anchors, centers)
    return sum(rational(w)*squared_exact(x,centers[j]) for x,w,j in zip(anchors,weights,labels))
