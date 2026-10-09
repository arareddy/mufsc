from fractions import Fraction
from collections import Counter

import numpy as np
import pytest

from rational_oracle import categorical, seed_indices, tape
from rng import canonical_tape, random_below
from kmeanspp import _weighted_choice, weighted_kmeanspp


class RawWords:
    def __init__(self, words):
        self.words = iter(words)
        self.calls = 0
        self.bit_generator = self
    def random_raw(self):
        self.calls += 1
        return next(self.words)


@pytest.mark.parametrize("W", list(range(1, 19)) + [31, 32, 33, 65])
def test_each_uniform_accepted_residue_is_represented_once(W):
    # Exhaustive finite support plus rejection-prefix checks; not frequencies.
    for u in range(W):
        words = RawWords([u])
        assert random_below(W, words) == u
        assert words.calls == (0 if W == 1 else 1)
    bits = (W - 1).bit_length()
    for reject in range(W, 1 << bits):
        words = RawWords([reject, 0])
        assert random_below(W, words) == 0
        assert words.calls == 2


def test_multiword_low_to_high_masking_and_rejection():
    W = 2 ** 64 + 3
    words = RawWords([2, 1])
    assert random_below(W, words) == 2 ** 64 + 2
    assert words.calls == 2
    words = RawWords([3, 1, 7, 2])
    assert random_below(W, words) == 7  # high second trial word masked to low bit
    assert words.calls == 4
    words = RawWords([(1 << 64) - 1, (1 << 64) - 1, 2, 0])
    assert random_below(W, words) == 2


@pytest.mark.parametrize("masses,integer_widths", [
    ([Fraction(1, 3)] * 3, [1, 1, 1]),
    ([Fraction(0), Fraction(1, 7), Fraction(0), Fraction(2, 7)], [0, 1, 0, 2]),
    ([Fraction(2, 3), Fraction(4, 9), Fraction(2, 9)], [3, 2, 1]),
])
def test_rational_cdf_exact_boundaries_and_gcd(masses, integer_widths):
    labels = [_weighted_choice(masses, RawWords([u])) for u in range(sum(integer_widths))]
    counts = Counter(labels)
    assert [counts[i] for i in range(len(masses))] == integer_widths
    assert labels == [i for i, count in enumerate(integer_widths) for _ in range(count)]


def test_historically_lost_positive_mass_remains_selectable():
    mass = [Fraction(1), Fraction(1, 2 ** 54), Fraction(1)]
    assert _weighted_choice(mass, RawWords([2 ** 54])) == 1
    assert _weighted_choice([Fraction(1, 2 ** 1074), 0, 0], RawWords([])) == 0


@pytest.mark.parametrize("mass", [[], [0, 0], [-1, 2], [float("nan"), 1], [float("inf"), 1]])
def test_invalid_categorical_masses_rejected(mass):
    with pytest.raises((ValueError, OverflowError)):
        _weighted_choice(mass, RawWords([0]))


def test_zero_mass_and_saturated_completion_consumes_no_bits():
    X = np.array([[3.], [2.], [1.]])
    for k, expected in [(0, []), (3, [0, 1, 2]), (5, [0, 1, 2, 0, 1])]:
        assert weighted_kmeanspp(X, [0, 1, 0], k, RawWords([])).tolist() == expected
    assert weighted_kmeanspp(X, [0, 0, 0], 2, RawWords([])).tolist() == [0, 1]
    with pytest.raises(ValueError):
        weighted_kmeanspp(np.empty((0, 1)), [], 1, RawWords([]))


@pytest.mark.parametrize("case", range(12))
def test_seeding_and_bit_consumption_match_independent_exact_oracle(case):
    rng = np.random.default_rng(case + 751)
    points = (rng.integers(-30, 30, (11, 2)) / 4096.).tolist()
    points[3] = points[1]
    weights = [Fraction(i % 4, 3 + i % 3) for i in range(11)]
    actual_rng, expected_rng = canonical_tape(case, "server"), tape(case, "server")
    actual = weighted_kmeanspp(np.array(points), weights, 5, actual_rng).tolist()
    expected = seed_indices(points, weights, 5, expected_rng)
    assert actual == expected
    assert [int(actual_rng.bit_generator.random_raw()) for _ in range(5)] == [
        int(expected_rng.bit_generator.random_raw()) for _ in range(5)]


@pytest.mark.parametrize("role,entities", [("local", (7, 0)), ("local", (7, 1)),
                                         ("server", ()), ("centralized", ())])
def test_keyed_tapes_match_declared_raw_protocol(role, entities):
    prod, oracle = canonical_tape(319, role, *entities), tape(319, role, *entities)
    assert [int(prod.bit_generator.random_raw()) for _ in range(9)] == [
        int(oracle.bit_generator.random_raw()) for _ in range(9)]
