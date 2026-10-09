"""Independent exact stress cases for the optimized squared-distance filter.

No production enclosure is used as the reference. Every expected distance
is a separately evaluated Fraction sum over actual represented coordinates.
"""
from fractions import Fraction
import math

import numpy as np
import pytest

from rational_oracle import assignment, squared_distance
from assignment import assign_all
from certificates import basic_certificate_vec, runner_up_certificate_vec
from exact_numeric import norm_bounds, squared_bounds
from unlearn import _center_shift


def inputs(d, pattern):
    if pattern == "all_zero":
        return np.zeros(d), np.zeros(d)
    if pattern == "square_underflow_accumulates":
        # Every rounded coordinate square is zero although the exact total
        # at d4096 is a nonzero representable subnormal squared distance.
        return np.full(d, math.ldexp(1., -538)), np.zeros(d)
    if pattern == "minimum_subnormal_difference":
        return np.full(d, math.ldexp(1., -1074)), np.zeros(d)
    if pattern == "half_subnormal_square_threshold":
        return np.full(d, np.nextafter(math.ldexp(1., -537), 0.)), np.zeros(d)
    if pattern == "maximum_domain_opposite_signs":
        return np.full(d, math.ldexp(1., 450)), np.full(d, -math.ldexp(1., 450))
    if pattern == "large_near_cancellation":
        high = math.ldexp(1., 450)
        return np.full(d, high), np.full(d, np.nextafter(high, 0.))
    if pattern == "mixed_exponents":
        exponents = [-1074, -1073, -1022, -539, -538, -537, -536, -512, -30, 0, 449, 450]
        a = np.array([math.ldexp((-1.) ** i, exponents[i % len(exponents)]) for i in range(d)])
        b = np.array([math.ldexp((-1.) ** (i + 1), exponents[(i * 7) % len(exponents)]) for i in range(d)])
        return a, b
    if pattern == "huge_plus_tiny_lost_terms":
        a = np.full(d, math.ldexp(1., -30))
        a[0] = math.ldexp(1., 450)
        return a, np.zeros(d)
    raise AssertionError(pattern)


PATTERNS = ["all_zero", "square_underflow_accumulates", "minimum_subnormal_difference",
            "half_subnormal_square_threshold", "maximum_domain_opposite_signs",
            "large_near_cancellation", "mixed_exponents", "huge_plus_tiny_lost_terms"]


@pytest.mark.parametrize("d", [1, 17, 4096])
@pytest.mark.parametrize("pattern", PATTERNS)
def test_fast_filter_encloses_exact_fraction_distance_at_numeric_boundaries(d, pattern):
    a, b = inputs(d, pattern)
    exact = squared_distance(a.tolist(), b.tolist())
    lo, hi = squared_bounds(a[None, :], b[None, :])
    assert math.isfinite(float(lo[0])) and math.isfinite(float(hi[0]))
    assert Fraction(float(lo[0])) <= exact <= Fraction(float(hi[0]))
    norm = norm_bounds(a[None, :], b[None, :])
    assert Fraction(float(norm.lower[0])) ** 2 <= exact <= Fraction(float(norm.upper[0])) ** 2
    if pattern == "all_zero":
        assert lo[0] == hi[0] == norm.lower[0] == norm.upper[0] == 0


@pytest.mark.parametrize("seed", [0, 1, 7, 33])
def test_full_dimension_random_dyadic_broadcast_enclosures(seed):
    rng = np.random.default_rng(seed)
    # All mantissas are represented exactly; high exponents stay inside 2^450.
    exponent_choices = np.array([-1074, -1070, -1022, -539, -537, -535, -128, -1, 0, 52, 448])
    a = np.ldexp(rng.choice(np.array([-1., 0., .5, 1.]), size=(2, 4096)),
                 rng.choice(exponent_choices, size=(2, 4096)))
    b = np.ldexp(rng.choice(np.array([-1., 0., .5, 1.]), size=(3, 4096)),
                 rng.choice(exponent_choices, size=(3, 4096)))
    low, high = squared_bounds(a[:, None, :], b[None, :, :])
    for i in range(len(a)):
        for j in range(len(b)):
            exact = squared_distance(a[i].tolist(), b[j].tolist())
            assert Fraction(float(low[i, j])) <= exact <= Fraction(float(high[i, j]))


@pytest.mark.parametrize("exponent", [-538, -30, 0, 449])
def test_full_dimension_assignments_and_certificates_against_rational_oracle(exponent):
    d, scale = 4096, math.ldexp(1., exponent)
    origin = np.zeros(d)
    close = np.full(d, scale)
    farther = close.copy()
    farther[-1] = np.nextafter(farther[-1], np.inf)
    X = np.stack([origin, close, -close])
    old = np.stack([farther, close, -close])
    # Swapping the almost coincident first two indexed centers forces the
    # lower-precision filter to defer to exact order and prevents false ties.
    new = old[[1, 0, 2]].copy()
    expected, second = assignment(X.tolist(), old.tolist())
    labels, d1, d2, runners = assign_all(X, old)
    assert labels.tolist() == expected
    assert runners.tolist() == second
    true_new, _ = assignment(X.tolist(), new.tolist())
    delta = _center_shift(new, old)
    for passes in [basic_certificate_vec(d1, d2, labels, delta),
                   runner_up_certificate_vec(d1, d2, labels, runners, delta)]:
        for i, passed in enumerate(passes):
            if passed:
                assert expected[i] == true_new[i]


def test_outside_declared_assignment_numeric_domain_is_rejected():
    with pytest.raises(ValueError, match="bound"):
        assign_all(np.array([[np.nextafter(math.ldexp(1., 450), np.inf)]]), np.array([[0.]]))
    with pytest.raises(ValueError, match="dimension"):
        assign_all(np.zeros((1, 4097)), np.zeros((1, 4097)))
