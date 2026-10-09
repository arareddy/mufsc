"""P0.4/P0.5: degenerate and edge-case unit tests -- empty slices, a slice
emptied by deletion, rejection of a full-group deletion, k exceeding the
number of available points, coincident points / zero D^2 mass, quantization
collisions, and nearest-center ties.
"""
import numpy as np
import pytest

from assignment import assign_all
from kmeanspp import ordinary_kmeanspp, weighted_kmeanspp
from rng import canonical_tape
from splitgroup import SplitGroupConfig, local_slice_step, snap_gamma
from train import train_full
from unlearn import unlearn


def _tiny_federation():
    client_data = {
        0: np.array([[0.0, 0.0], [0.2, 0.1], [-0.1, 0.3], [5.0, 5.0]]),  # pure group A
        1: np.array([[10.0, 10.0], [10.1, 9.9]]),  # pure group B
        2: np.array([[3.0, 3.0], [3.1, 2.9], [8.0, 8.0]]),  # mixed: A, B, B
    }
    group_of = {
        0: np.array([0, 0, 0, 0]),
        1: np.array([1, 1]),
        2: np.array([0, 1, 1]),
    }
    return client_data, group_of


def test_empty_local_slice_not_in_slice_results():
    client_data, group_of = _tiny_federation()
    ckpt = train_full(client_data, group_of, seed=1, k=2, T=1, L=2)
    assert (0, 1) not in ckpt["slice_results"]  # client 0 has no group-B points
    assert (1, 0) not in ckpt["slice_results"]  # client 1 has no group-A points
    assert (0, 0) in ckpt["slice_results"]
    assert (2, 0) in ckpt["slice_results"]
    assert (2, 1) in ckpt["slice_results"]


def test_touched_slice_emptied_by_deletion_is_dropped():
    client_data, group_of = _tiny_federation()
    ckpt = train_full(client_data, group_of, seed=1, k=2, T=1, L=2)
    removed = {2: np.array([0])}  # client 2's sole group-A point
    res = unlearn(ckpt, removed, certificate_mode="runnerup")
    assert (2, 0) not in res["slice_results"]
    assert (2, 1) in res["slice_results"]


def test_full_group_deletion_is_rejected():
    client_data, group_of = _tiny_federation()
    ckpt = train_full(client_data, group_of, seed=1, k=2, T=1, L=2)
    removed = {1: np.array([0, 1]), 2: np.array([1, 2])}  # empties group B entirely
    with pytest.raises(ValueError):
        unlearn(ckpt, removed, certificate_mode="runnerup")


def test_k_exceeds_available_points_canonical_completion():
    X = np.array([[0.0, 0.0], [1.0, 1.0]])
    rng = canonical_tape(1, "local", 0, 0)
    idx = ordinary_kmeanspp(X, k=5, rng=rng)
    assert len(idx) == 5
    assert set(idx.tolist()) <= {0, 1}  # only two distinct points exist


def test_all_points_coincident_zero_d2_mass_completes_deterministically():
    X = np.tile(np.array([[2.0, -1.0]]), (4, 1))
    rng = canonical_tape(1, "local", 0, 0)
    idx = ordinary_kmeanspp(X, k=3, rng=rng)
    assert len(idx) == 3  # zero D^2 potential after the first pick: must not crash

    weights = np.array([1.0, 1.0, 1.0, 1.0])
    rng2 = canonical_tape(2, "server")
    idx_w = weighted_kmeanspp(X, weights, k=3, rng=rng2)
    assert len(idx_w) == 3


def test_zero_weight_points_never_chosen_by_sampling_but_can_be_completed_into():
    X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    weights = np.array([1.0, 0.0, 0.0])  # only one point can ever be sampled
    rng = canonical_tape(3, "server")
    idx = weighted_kmeanspp(X, weights, k=1, rng=rng)
    assert idx[0] == 0


def test_snap_gamma_produces_a_genuine_collision():
    reps = np.array([[0.001, 0.0], [0.002, 0.0], [5.0, 5.0]])
    anchors = snap_gamma(reps, gamma=1.0)
    assert np.array_equal(anchors[0], anchors[1])
    assert not np.array_equal(anchors[0], anchors[2])


def test_local_slice_step_conserves_total_multiplicity_under_quantization():
    X = np.array([[0.001, 0.0], [0.002, 0.0], [5.0, 5.0], [5.001, 5.0]])
    cfg = SplitGroupConfig(k=2, gamma=0.1)
    res = local_slice_step(X, seed=3, client_id=0, group_id=0, cfg=cfg)
    assert int(res["mult"].sum()) == X.shape[0]


def test_nearest_center_tie_breaks_to_lowest_index():
    X = np.array([[0.0, 0.0]])
    centers = np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 5.0]])  # centers 0,1 equidistant
    labels, d1, d2, runner_up = assign_all(X, centers)
    assert labels[0] == 0
    assert runner_up[0] == 1
    assert d1[0] == pytest.approx(1.0)
    assert d2[0] == pytest.approx(1.0)
