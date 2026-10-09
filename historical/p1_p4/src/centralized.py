"""Centralized weighted k-means++: a non-federated quality reference (never
a runtime baseline -- it has no client compression, no communication, and
would not be a legal deployment). Weighted k-means++ run directly on the
pooled represented dataset with the correct global weight 1/n_g(x). It is a stochastic quality reference, not a per-seed upper bound; used
only to check where warm-start quality slack enters, never timed.
"""
import numpy as np
from fractions import Fraction

from kmeanspp import weighted_kmeanspp
from rng import canonical_tape


def run_centralized(client_data: dict, group_of: dict, seed: int, k: int) -> np.ndarray:
    keys = sorted(client_data.keys())
    X = np.concatenate([client_data[c] for c in keys], axis=0)
    g = np.concatenate([group_of[c] for c in keys], axis=0)
    n_A, n_B = int(np.sum(g == 0)), int(np.sum(g == 1))
    if n_A == 0 or n_B == 0: raise ValueError("both global groups required")
    weights = [Fraction(1, n_A if int(v)==0 else n_B) for v in g]
    tape = canonical_tape(seed, "centralized")
    idx = weighted_kmeanspp(X, weights, k, tape)
    return X[idx].copy()
