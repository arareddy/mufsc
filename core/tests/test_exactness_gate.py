"""P0.1: the core exactness gate. Independent fresh training and replay must
agree at *every round* on indexed centers and exact (N,S,SS) -- checked via
the per-round digest, which hashes both, so no permutation matching or
tolerance can silently pass a mismatch. Covers all three replay modes and
two deletion-sensitive seeds: a locally selected representative, and an
entire high-multiplicity anchor's underlying points.
"""
import numpy as np
import pytest

from assignment import assign_labels_only
from helpers import apply_removal, make_federation
from train import train_full
from unlearn import unlearn

CONFIGS = [
    dict(seed=1, k=3, T=3, L=4, gamma=0.0),
    dict(seed=2, k=2, T=4, L=3, gamma=0.05),
    dict(seed=3, k=4, T=3, L=5, gamma=0.1),
]


def _random_removal(client_data, seed, frac=0.15):
    r = np.random.default_rng(seed)
    removed = {}
    for c, X_c in client_data.items():
        n_c = X_c.shape[0]
        n_rm = int(n_c * frac)
        if 0 < n_rm < n_c:
            removed[c] = r.choice(n_c, size=n_rm, replace=False)
    return removed


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda c: f"s{c['seed']}_k{c['k']}")
@pytest.mark.parametrize("mode", ["none", "basic", "runnerup"])
def test_replay_matches_fresh_training_exactly(cfg, mode):
    client_data, group_of = make_federation(seed=cfg["seed"])
    ckpt = train_full(client_data, group_of, cfg["seed"], cfg["k"], cfg["T"], cfg["L"], gamma=cfg["gamma"])

    removed = _random_removal(client_data, seed=cfg["seed"] + 100)
    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, cfg["seed"], cfg["k"], cfg["T"], cfg["L"], gamma=cfg["gamma"])

    res = unlearn(ckpt, removed, certificate_mode=mode)
    assert res["digests"] == fresh["digests"]
    assert np.array_equal(res["final_centers"], fresh["final_centers"])


@pytest.mark.parametrize("mode", ["basic", "runnerup"])
def test_deleting_a_selected_representative_still_matches(mode):
    client_data, group_of = make_federation(seed=11)
    seed, k, T, L = 11, 3, 3, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)

    (c, g), res0 = next(iter(ckpt["slice_results"].items()))
    local_idx_in_slice = int(res0["selected_idx"][0])
    slice_positions = np.where(group_of[c] == g)[0]
    removed = {c: np.array([slice_positions[local_idx_in_slice]])}

    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k, T, L, gamma=0.0)
    replay = unlearn(ckpt, removed, certificate_mode=mode)
    assert replay["digests"] == fresh["digests"]


@pytest.mark.parametrize("mode", ["basic", "runnerup"])
def test_deleting_the_highest_multiplicity_anchor_still_matches(mode):
    client_data, group_of = make_federation(seed=12)
    seed, k, T, L = 12, 3, 3, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)

    (c, g), res0 = max(ckpt["slice_results"].items(), key=lambda kv: kv[1]["mult"].max())
    top_anchor_j = int(np.argmax(res0["mult"]))
    X_slice = client_data[c][group_of[c] == g]
    reps = X_slice[res0["selected_idx"]]
    labels_in_slice = assign_labels_only(X_slice, reps)
    slice_positions = np.where(group_of[c] == g)[0]
    removed = {c: slice_positions[labels_in_slice == top_anchor_j]}

    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k, T, L, gamma=0.0)
    replay = unlearn(ckpt, removed, certificate_mode=mode)
    assert replay["digests"] == fresh["digests"]


def test_empty_removal_reproduces_training_bit_for_bit():
    client_data, group_of = make_federation(seed=13)
    seed, k, T, L = 13, 3, 3, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.02)
    for mode in ("none", "basic", "runnerup"):
        res = unlearn(ckpt, {}, certificate_mode=mode)
        assert res["digests"] == ckpt["digests"]
        assert np.array_equal(res["final_centers"], ckpt["final_centers"])


def test_k_equals_one_edge_case_matches():
    client_data, group_of = make_federation(seed=14)
    seed = 14
    ckpt = train_full(client_data, group_of, seed, k=1, T=2, L=4, gamma=0.0)
    removed = _random_removal(client_data, seed=seed + 100)
    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k=1, T=2, L=4, gamma=0.0)
    for mode in ("none", "basic", "runnerup"):
        res = unlearn(ckpt, removed, certificate_mode=mode)
        assert res["digests"] == fresh["digests"]
