"""Shared synthetic-federation builders for the P0 suite. Not a test module
itself (no test_ prefix), just fixtures the test files import.
"""
import numpy as np


def make_federation(n_clients=6, d=3, seed=0, n_lo=30, n_hi=80,
                     cluster_scale=5.0, noise=0.7, n_true_clusters=3):
    r = np.random.default_rng(seed)
    client_data, group_of = {}, {}
    for c in range(n_clients):
        n_c = int(r.integers(n_lo, n_hi))
        if c % 3 == 0:
            g = np.zeros(n_c, dtype=np.int64)  # pure group A
        elif c % 3 == 1:
            g = np.ones(n_c, dtype=np.int64)  # pure group B
        else:
            g = r.integers(0, 2, size=n_c)  # mixed
        centers = r.normal(scale=cluster_scale, size=(n_true_clusters, d))
        X = centers[r.integers(0, n_true_clusters, size=n_c)] + r.normal(scale=noise, size=(n_c, d))
        client_data[c] = X
        group_of[c] = g
    return client_data, group_of


def apply_removal(client_data: dict, group_of: dict, removed: dict) -> tuple:
    new_cd, new_g = {}, {}
    for c, X_c in client_data.items():
        rem = removed.get(c, np.array([], dtype=np.int64))
        mask = np.ones(X_c.shape[0], dtype=bool)
        mask[rem] = False
        new_cd[c] = X_c[mask]
        new_g[c] = group_of[c][mask]
    return new_cd, new_g
