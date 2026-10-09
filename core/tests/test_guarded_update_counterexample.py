"""P0.2: the non-dyadic fair-optimum instance, A={-1,1}, B={3}, k=1.

Verifies: the exact optimum is c*=4/3 with F(c*)=25/9; accepting an
unguarded one-step bisection candidate (lambda=0.5 -> c=1.5) would strictly
increase the objective; GFU_L, started at the optimum, never does.
"""
import numpy as np

from fair_update import group_delta, group_means, group_objective, guarded_fair_update
from fixedpoint import FixedPointConfig, accumulate_stats, quantize


def _build_stats():
    cfg = FixedPointConfig(scale_bits=20, clip=8.0)
    X = np.array([[-1.0], [1.0], [3.0]])
    group_idx = np.array([0, 0, 1], dtype=np.int64)
    labels = np.array([0, 0, 0], dtype=np.int64)  # k=1: everything in the one cluster
    X_int = quantize(X, cfg)
    N, S, SS = accumulate_stats(X_int, group_idx, labels, num_groups=2, k=1)
    return N, S, SS, cfg


def _objectives(N, S, SS, cfg):
    mu = group_means(N, S, 1, cfg.scale)
    delta_A = group_delta(N[0], S[0], SS[0], n_g=2, k=1, scale=cfg.scale)
    delta_B = group_delta(N[1], S[1], SS[1], n_g=1, k=1, scale=cfg.scale)

    def f_a(c):
        return group_objective(np.array([[c]]), mu[0], [1.0], delta_A, 1)

    def f_b(c):
        return group_objective(np.array([[c]]), mu[1], [1.0], delta_B, 1)

    return f_a, f_b


def test_exact_optimum_is_four_thirds():
    N, S, SS, cfg = _build_stats()
    f_a, f_b = _objectives(N, S, SS, cfg)
    c_star = 4.0 / 3.0
    assert abs(f_a(c_star) - f_b(c_star)) < 1e-9
    assert abs(f_a(c_star) - 25.0 / 9.0) < 1e-9


def test_unguarded_one_step_bisection_would_increase_the_objective():
    N, S, SS, cfg = _build_stats()
    f_a, f_b = _objectives(N, S, SS, cfg)
    c_star = 4.0 / 3.0
    F_star = max(f_a(c_star), f_b(c_star))

    lam = 0.5  # the single bisection midpoint at L=1
    c_candidate = 3.0 * (1.0 - lam)
    assert abs(c_candidate - 1.5) < 1e-12
    F_candidate = max(f_a(c_candidate), f_b(c_candidate))

    assert F_candidate > F_star  # accepting it unconditionally is unsound


def test_guarded_fair_update_never_increases_the_objective_here():
    N, S, SS, cfg = _build_stats()
    centers = np.array([[4.0 / 3.0]])
    new_centers, info = guarded_fair_update(centers, N, S, SS, n_A=2, n_B=1, k=1, L=1, scale=cfg.scale)
    assert np.array_equal(new_centers, centers)
    assert info["accepted"] is False


def test_guarded_fair_update_matches_optimum_from_a_worse_start():
    """Starting away from the optimum, the guard should still let genuine
    improvement through (monotonicity is one-directional, not a freeze)."""
    N, S, SS, cfg = _build_stats()
    centers = np.array([[3.0]])  # mu_B: far from optimal, F(3)=max(1+9,0)=10
    new_centers, info = guarded_fair_update(centers, N, S, SS, n_A=2, n_B=1, k=1, L=20, scale=cfg.scale)
    f_a, f_b = _objectives(N, S, SS, cfg)
    new_val = max(f_a(float(new_centers[0, 0])), f_b(float(new_centers[0, 0])))
    assert new_val <= max(f_a(3.0), f_b(3.0))
    assert abs(float(new_centers[0, 0]) - 4.0 / 3.0) < 1e-4  # L=20 resolves well past 1e-4
