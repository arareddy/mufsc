"""P0 Experiment 0, item 4 ("fair cells: neither group in a cell; only one
group; coincident means; equality f_A=f_B at a candidate") -- the branches
in _lambda_center and the final tie-break rule, each exercised directly.

Also covers the specific interaction the kmeanspp k>=n fix (P0 caught a bug
where it returned fewer than k indices) made newly reachable: canonical
duplicate-index completion can put two representatives at the identical
location, so one of them never wins an assignment tie and its cell is
permanently empty for the rest of training -- exactly the "neither group"
branch, now reachable from ordinary training, not just a hand-built stats
tuple.
"""
import numpy as np

from fair_update import _lambda_center, guarded_fair_update
from fixedpoint import FixedPointConfig, accumulate_stats, quantize
from helpers import apply_removal, make_federation
from train import train_full
from unlearn import unlearn

OLD = np.array([9.0, 9.0])


def test_neither_group_occupies_the_cell_retains_old_center():
    for lam in (0.0, 0.5, 1.0):
        c = _lambda_center(None, None, 0.0, 0.0, lam, OLD)
        assert np.array_equal(c, OLD)


def test_only_group_a_occupies_the_cell_candidate_is_group_a_mean():
    mu_a = [1.0, 2.0]
    for lam in (0.0, 0.3, 1.0):
        c = _lambda_center(mu_a, None, 0.6, 0.0, lam, OLD)
        assert np.allclose(c, mu_a)


def test_only_group_b_occupies_the_cell_candidate_is_group_b_mean():
    mu_b = [-1.0, 4.0]
    for lam in (0.0, 0.7, 1.0):
        c = _lambda_center(None, mu_b, 0.0, 0.6, lam, OLD)
        assert np.allclose(c, mu_b)


def test_coincident_means_candidate_equals_the_shared_mean_at_any_weight():
    mu = [3.0, -2.0]
    for lam in (0.0, 0.25, 0.5, 0.75, 1.0):
        c = _lambda_center(mu, mu, 0.4, 0.6, lam, OLD)
        assert np.allclose(c, mu)


def test_tie_break_at_equal_objective_picks_the_smallest_lambda():
    """A={-1,1} (mean 0, Delta=1), B={3,5} (mean 4, Delta=1), k=1: by
    symmetry F(c(0))=F(c(1))=17 exactly. With L=0 only the two endpoints
    are ever evaluated, so this isolates the final "smallest encoded
    lambda wins ties" rule with no bisection-loop ambiguity."""
    cfg = FixedPointConfig(scale_bits=20, clip=8.0)
    X = np.array([[-1.0], [1.0], [3.0], [5.0]])
    group_idx = np.array([0, 0, 1, 1], dtype=np.int64)
    labels = np.zeros(4, dtype=np.int64)
    X_int = quantize(X, cfg)
    N, S, SS = accumulate_stats(X_int, group_idx, labels, num_groups=2, k=1)

    centers = np.array([[100.0]])  # deliberately bad, so the guard accepts the tie winner
    new_centers, info = guarded_fair_update(centers, N, S, SS, n_A=2, n_B=2, k=1, L=0, scale=cfg.scale)

    assert info["accepted"] is True
    assert info["lambda"] == 0.0
    assert abs(float(new_centers[0, 0]) - 4.0) < 1e-9  # c(0) = 4*(1-0) = 4


def test_duplicate_anchor_from_canonical_completion_freezes_an_empty_cell():
    """k larger than the number of distinct points forces kmeanspp's
    canonical-duplicate completion (fixed in this P0 pass -- it used to
    return too few indices). A duplicate center never wins an assignment
    tie against its lower-index twin, so its cell is empty every round;
    GFU_L must retain it unchanged rather than crash or drift, and the
    whole pipeline must still replay exactly."""
    client_data = {0: np.array([[0.0, 0.0], [0.1, 0.0]]), 1: np.array([[5.0, 5.0], [5.1, 5.0]])}
    group_of = {0: np.array([0, 0]), 1: np.array([1, 1])}
    seed, k, T, L = 51, 5, 3, 4  # k=5 with only 4 total points, 2 per group

    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)
    for t in range(len(ckpt["trajectory"]) - 1):
        # at least one center must be frozen (identical across consecutive
        # rounds) given far more clusters than distinct data locations
        shifts = np.linalg.norm(ckpt["trajectory"][t + 1] - ckpt["trajectory"][t], axis=1)
        assert np.any(shifts == 0.0)

    removed = {0: np.array([0])}
    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k, T, L, gamma=0.0)
    for mode in ("none", "basic", "runnerup"):
        res = unlearn(ckpt, removed, certificate_mode=mode)
        assert res["digests"] == fresh["digests"]
