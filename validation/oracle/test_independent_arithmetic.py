from fractions import Fraction
import pickle

import numpy as np
import pytest

from rational_oracle import (assignment, candidate, encode, fair_update, group_objectives,
                             hex_centers, squared_distance, stats)
from assignment import assign_all, assign_labels_only
from certificates import basic_certificate_vec, runner_up_certificate_vec
from fair_update import guarded_fair_update
from fixedpoint import FixedPointConfig, accumulate_stats, quantize
from train import train_full
from unlearn import _center_shift, unlearn


@pytest.mark.parametrize("power", [-300, -150, -30, 0, 30, 130])
def test_assignment_against_rational_distance_order(power):
    rng = np.random.default_rng(831)
    X = rng.normal(size=(29, 3)) * 10. ** power
    C = rng.normal(size=(7, 3)) * 10. ** power
    C[6] = C[2]
    expected, runners = assignment(X.tolist(), C.tolist())
    labels, d1, d2, runner = assign_all(X, C)
    assert labels.tolist() == expected
    assert runner.tolist() == runners
    assert assign_labels_only(X, C).tolist() == expected
    for distance, ids in [(d1, labels), (d2, runner)]:
        assert hasattr(distance, "lower") and hasattr(distance, "upper")
        for i, j in enumerate(ids):
            exact = squared_distance(X[i], C[j])
            lower, upper = float(distance.lower[i]), float(distance.upper[i])
            assert lower >= 0
            assert Fraction(lower) ** 2 <= exact
            assert np.isinf(upper) or exact <= Fraction(upper) ** 2


def test_nearest_center_rounding_is_not_a_tie():
    X, C = np.zeros((1, 2)), np.array([[1., 2. ** -30], [1., 0.]])
    assert assign_all(X, C)[0].tolist() == [1]
    assert assign_labels_only(X, C).tolist() == [1]
    C = np.array([[1., 0.], [-1., 0.], [1., 0.]])
    assert assign_all(X, C)[0].tolist() == [0]
    assert assign_all(X, C)[3].tolist() == [1]


def test_certificates_reject_underflow_false_positive():
    lo, hi = 1e-150, np.nextafter(1e-150, np.inf)
    X, old = np.zeros((1, 1)), np.array([[lo], [hi]])
    new = old[::-1].copy()
    labels, d1, d2, runners = assign_all(X, old)
    assert labels.tolist() != assignment(X.tolist(), new.tolist())[0]
    delta = _center_shift(new, old)
    assert not basic_certificate_vec(d1, d2, labels, delta).any()
    assert not runner_up_certificate_vec(d1, d2, labels, runners, delta).any()


def test_bounds_survive_slice_and_pickle():
    X, C = np.array([[0.], [1.], [2.]]), np.array([[0.], [2.]])
    _, d1, _, _ = assign_all(X, C)
    copy = pickle.loads(pickle.dumps(d1))
    for selected in [np.array([True, False, True]), np.array([2, 0]), slice(1, 3)]:
        assert np.array_equal(copy[selected].lower, d1.lower[selected])
        assert np.array_equal(copy[selected].upper, d1.upper[selected])


def test_certificates_sound_against_independent_labels_on_adversarial_geometries():
    rng = np.random.default_rng(718)
    checks, passed_count = 0, [0, 0]
    geometries = [(np.array([[0.]]), np.array([[0.], [1.]]), np.array([[0.], [101.]])),
                  (np.array([[0.]]), np.array([[0.], [10.], [11.]]), np.array([[.5], [10.], [.1]]))]
    for scale in [1., 1e-150, 1e-300, 1e100]:
        for shift in [0., 1e-15, .01, 1., 50.]:
            old = rng.normal(size=(5, 3)) * scale
            X = rng.normal(size=(17, 3)) * scale
            new = old + rng.normal(size=old.shape) * shift * scale
            geometries.append((X, old, new))
    for X, old, new in geometries:
        labels, d1, d2, runners = assign_all(X, old)
        true_old, _ = assignment(X.tolist(), old.tolist())
        true_new, _ = assignment(X.tolist(), new.tolist())
        assert labels.tolist() == true_old
        delta = _center_shift(new, old)
        for mode, passes in enumerate([basic_certificate_vec(d1, d2, labels, delta),
                    runner_up_certificate_vec(d1, d2, labels, runners, delta)]):
            for i, passed in enumerate(passes):
                checks += 1
                if passed:
                    passed_count[mode] += 1
                    assert true_old[i] == true_new[i]
    assert checks > 600
    assert min(passed_count) > 0


@pytest.mark.parametrize("bits,L", [(12, 6), (16, 20)])
def test_represented_guard_and_branches_match_independent_oracle(bits, L):
    rng = np.random.default_rng(802)
    for case in range(28):
        n, d, k = 11 + case % 8, 1 + case % 3, 1 + case % 5
        integers = rng.integers(-7 * 2 ** bits, 7 * 2 ** bits, (n, d)).tolist()
        groups = [0, 1] + rng.integers(0, 2, n - 2).tolist()
        # Random fixed partitions deliberately create empty and one-group cells.
        labels = rng.integers(0, k, n).tolist()
        N, S, SS = stats(integers, groups, labels, k)
        old = rng.normal(size=(k, d)) * 5
        counts = [groups.count(0), groups.count(1)]
        expected, info = fair_update(old.tolist(), N, S, SS, counts, 2 ** bits, L)
        actual, prod = guarded_fair_update(old, N, S, SS, *counts, k, L, 2 ** bits)
        assert hex_centers(actual) == hex_centers(expected)
        assert prod["lambda"] == info["lambda"]
        assert prod["accepted"] == info["accepted"]
        assert [{"lambda": b["lambda"], "f_A": b["f_A"], "f_B": b["f_B"],
                 "branch": "lo" if b["lower"] else "hi"} for b in prod["branches"]] == info["branches"]
        assert max(group_objectives(actual, N, S, SS, counts, 2 ** bits)) <= max(
            group_objectives(old, N, S, SS, counts, 2 ** bits))


@pytest.mark.parametrize("bits,L", [(12, 6), (16, 20)])
def test_historical_guard_witness_is_rejected_or_corrected(bits, L):
    points = [[x * 2 ** bits] for x in [-7, -7, 2, 7, 6, -7, 3]]
    N, S, SS = stats(points, [0, 0, 0, 1, 1, 1, 1], [0] * 7, 1)
    optimum, _ = fair_update([[8.]], N, S, SS, [3, 4], 2 ** bits, L)
    for direction in [-np.inf, np.inf]:
        incumbent = np.array([[np.nextafter(optimum[0][0], direction)]])
        actual, _ = guarded_fair_update(incumbent, N, S, SS, 3, 4, 1, L, 2 ** bits)
        expected, _ = fair_update(incumbent.tolist(), N, S, SS, [3, 4], 2 ** bits, L)
        assert hex_centers(actual) == hex_centers(expected)
        assert max(group_objectives(actual, N, S, SS, [3, 4], 2 ** bits)) <= max(
            group_objectives(incumbent, N, S, SS, [3, 4], 2 ** bits))


@pytest.mark.parametrize("bits,L", [(12, 6), (16, 20)])
def test_one_represented_X_from_initialization_to_update(bits, L):
    data = {0: np.array([[1 / 3]]), 1: np.array([[1 / 3]])}
    groups = {0: np.array([0]), 1: np.array([1])}
    cfg = FixedPointConfig(bits, 8.)
    ck = train_full(data, groups, 1, 1, 2, L, fp_cfg=cfg)
    encoded = float(Fraction(round(Fraction(1 / 3) * 2 ** bits), 2 ** bits))
    assert all(hex_centers(c) == [[encoded.hex()]] for c in ck["trajectory"])
    assert float(data[0][0, 0]) == 1 / 3  # caller-owned data was not modified


@pytest.mark.parametrize("bits", [12, 16])
def test_encoding_ties_clips_and_bigint_aggregates(bits):
    scale = 2 ** bits
    points = [[-.5 / scale, .5 / scale], [1.5 / scale, 2.5 / scale], [-9., 9.], [1 / 3, -1 / 3]]
    expected = encode(points, bits, 8.)
    actual = quantize(np.array(points), FixedPointConfig(bits, 8.))
    assert actual.tolist() == expected
    giant = np.full((100, 1), 2 ** 29, dtype=np.int64)
    result = accumulate_stats(giant, np.zeros(100, dtype=int), np.zeros(100, dtype=int), 2, 1)
    assert result == stats(giant.tolist(), [0] * 100, [0] * 100, 1)


@pytest.mark.parametrize("bits,clip", [(-1, 8.), (1.2, 8.), (True, 8.), (16, 0.),
                                      (16, -1.), (16, np.inf), (16, np.nan), (63, 8.)])
def test_unsafe_fixedpoint_config_rejected(bits, clip):
    with pytest.raises((TypeError, ValueError)):
        cfg = FixedPointConfig(bits, clip)
        quantize(np.array([[1.]]), cfg)


def test_unsafe_point_square_rejected():
    with pytest.raises((ValueError, OverflowError)):
        accumulate_stats(np.array([[2 ** 32]], dtype=np.int64), np.array([0]), np.array([0]), 2, 1)


@pytest.mark.parametrize("removal", [{99: [0]}, {0: [-1]}, {0: [8]}, {0: [0, 0]},
                                     {0: [0.5]}, {0: [[0]]}, {0: [True]}])
def test_invalid_deletion_requests_rejected(removal):
    data = {0: np.array([[0.], [1.], [2.]]), 1: np.array([[3.], [4.], [5.]])}
    groups = {0: np.array([0, 1, 0]), 1: np.array([1, 0, 1])}
    ck = train_full(data, groups, 8, 2, 1, 6, fp_cfg=FixedPointConfig(12, 8.))
    with pytest.raises((TypeError, ValueError, IndexError)):
        unlearn(ck, {c: np.array(v) for c, v in removal.items()}, "none")


def test_existing_global_group_empty_rejection_preserved():
    ck = train_full({0: np.array([[0.], [1.]]), 1: np.array([[2.], [3.]])},
                    {0: np.array([0, 0]), 1: np.array([1, 1])}, 9, 2, 1, 6)
    for mode in ["none", "basic", "runnerup"]:
        with pytest.raises(ValueError, match="group"):
            unlearn(ck, {0: np.array([0, 1])}, mode)


@pytest.mark.parametrize("mode", ["basic", "runnerup"])
@pytest.mark.parametrize("threshold,abandoned", [(.5, False), (np.nextafter(.5, 0.), True),
                                                (np.nextafter(.5, 1.), False)])
def test_fallback_strict_half_boundary_with_only_real_passes(mode, threshold, abandoned, monkeypatch):
    import unlearn as module
    data = {0: np.zeros((4, 1)), 1: np.full((3, 1), 4.)}
    groups = {0: np.zeros(4, dtype=int), 1: np.ones(3, dtype=int)}
    ck = train_full(data, groups, 31, 2, 3, 6)
    original = module._certify
    calls = {"n": 0}
    def with_extra_failures(labels, d1, d2, runners, delta, k, certificate_mode):
        passes = original(labels, d1, d2, runners, delta, k, certificate_mode)
        assert passes.all()  # never invent a pass; conservatively force failures
        calls["n"] += 1
        return np.zeros_like(passes) if calls["n"] % 2 else passes
    monkeypatch.setattr(module, "_certify", with_extra_failures)
    actual = unlearn(ck, {0: np.array([0])}, mode, threshold)
    fresh = train_full({0: data[0][1:], 1: data[1]}, {0: groups[0][1:], 1: groups[1]}, 31, 2, 3, 6)
    assert actual["per_round_stats"] == fresh["per_round_stats"]
    assert [hex_centers(c) for c in actual["trajectory"]] == [hex_centers(c) for c in fresh["trajectory"]]
    assert (actual["abandonment_round"] == 0) == abandoned
    assert actual["diagnostics"][0]["A"] == 6
    assert actual["diagnostics"][0]["P"] == 3
    assert actual["diagnostics"][0]["S"] == (0 if abandoned else 3)
    assert actual["diagnostics"][0]["J"] == (3 if abandoned else 0)


def test_model_only_and_replay_cache_contract():
    data = {0: np.zeros((3, 1)), 1: np.full((3, 1), 4.)}
    groups = {0: np.zeros(3, dtype=int), 1: np.ones(3, dtype=int)}
    full = train_full(data, groups, 31, 2, 2, 6)
    model = train_full(data, groups, 31, 2, 2, 6, build_cache=False)
    assert model["cache_valid"] is False
    assert model["per_round_stats"] == full["per_round_stats"]
    assert [hex_centers(c) for c in model["trajectory"]] == [hex_centers(c) for c in full["trajectory"]]
    with pytest.raises(ValueError, match="checkpoint"):
        unlearn(model, {}, "none")
    replay = unlearn(full, {0: np.array([0])}, "basic")
    assert replay["cache_valid"] is False
    with pytest.raises(ValueError, match="checkpoint"):
        unlearn(replay, {}, "none")


def test_single_center_runner_sentinel_and_label():
    labels, d1, d2, runners = assign_all(np.array([[0.], [1.]]), np.array([[2.]]))
    assert labels.tolist() == [0, 0]
    assert runners.tolist() == [-1, -1]
    assert np.isposinf(d2).all()
