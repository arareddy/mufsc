"""P0.6: force certificate abandonment and verify the discard-and-rebuild
path still matches fresh retraining exactly regardless of which round (or
whether) it fires, and that once triggered it stays in effect for every
remaining round (discarded exactly once, not flapping)."""
import numpy as np
import pytest

import unlearn as unlearn_module
from helpers import apply_removal, make_federation
from train import train_full
from unlearn import unlearn


@pytest.mark.parametrize("threshold", [0.0, 0.3, 1.1])  # 1.1: never fires
@pytest.mark.parametrize("mode", ["basic", "runnerup"])
def test_abandonment_at_various_thresholds_still_matches(threshold, mode):
    client_data, group_of = make_federation(seed=21)
    seed, k, T, L = 21, 3, 5, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)

    r = np.random.default_rng(999)
    removed = {}
    for c, X_c in client_data.items():
        n_c = X_c.shape[0]
        n_rm = max(1, n_c // 4)
        removed[c] = r.choice(n_c, size=min(n_rm, n_c - 1), replace=False)

    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k, T, L, gamma=0.0)

    res = unlearn(ckpt, removed, certificate_mode=mode, abandon_threshold=threshold)
    assert res["digests"] == fresh["digests"]

    seen_abandoned = False
    for d in res["diagnostics"]:
        if seen_abandoned:
            assert d["abandoned_this_round"], "abandonment reverted on a later round"
        if d["abandoned_this_round"]:
            seen_abandoned = True

    if threshold <= 0.0:
        assert res["abandonment_round"] == 0
    if threshold > 1.0:
        assert res["abandonment_round"] is None


@pytest.mark.parametrize("trigger_round", range(5))
def test_abandonment_forced_at_every_possible_round_still_matches(trigger_round, monkeypatch):
    """'Force certification abandonment at each replay round' (Experiment 0,
    item 6): unlike the threshold-based tests above, this drives the
    trigger round directly, so every round -- not just 0 or 'never' -- is
    actually exercised as the abandonment point, including a round after
    real patch work has already happened."""
    # The corrected rational sampler changes the historical random fixture's
    # initializer, so seed31's old make_federation fixture now legitimately
    # abandons at round0. Use a geometrically certified stable fixture instead:
    # each group occupies exactly one location, each global group's total
    # server mass stays one, and deletion leaves both locations occupied.
    client_data = {0: np.array([[0.], [0.], [0.]]),
                   1: np.array([[4.], [4.], [4.]])}
    group_of = {0: np.array([0, 0, 0]), 1: np.array([1, 1, 1])}
    seed, k, T, L = 31, 2, 5, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)
    removed = {0: np.array([0])}
    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh = train_full(cd_r, g_r, seed, k, T, L, gamma=0.0)

    # Verify genuine pre-trigger certificate behavior before any monkeypatch.
    stable = unlearn(ckpt, removed, certificate_mode="basic", abandon_threshold=0.5)
    assert stable["abandonment_round"] is None
    assert all(d["certified"] == 5 for d in stable["diagnostics"])
    assert all(np.array_equal(a, b) for a, b in zip(ckpt["trajectory"], fresh["trajectory"]))

    num_clients = len(ckpt["client_ids"])
    threshold_calls = trigger_round * num_clients
    call_count = {"n": 0}
    real_certify = unlearn_module._certify

    def fake_certify(labels, d1, d2, runner_up, delta, k_, mode):
        call_count["n"] += 1
        if call_count["n"] > threshold_calls:
            return np.zeros(labels.shape, dtype=bool)  # force failure from here on
        # Genuinely certify earlier rounds -- faking a "pass" here would
        # skip a reassignment real correctness depends on and could make
        # the pre-trigger rounds silently wrong, not just untested.
        return real_certify(labels, d1, d2, runner_up, delta, k_, mode)

    monkeypatch.setattr(unlearn_module, "_certify", fake_certify)
    res = unlearn(ckpt, removed, certificate_mode="basic", abandon_threshold=0.5)

    assert res["digests"] == fresh["digests"]
    assert res["per_round_stats"] == fresh["per_round_stats"]
    assert res["abandonment_round"] == trigger_round
    for i, d in enumerate(res["diagnostics"]):
        assert d["abandoned_this_round"] == (i >= trigger_round)


def test_direct_replay_mode_is_abandoned_from_round_zero():
    client_data, group_of = make_federation(seed=22)
    seed, k, T, L = 22, 3, 3, 4
    ckpt = train_full(client_data, group_of, seed, k, T, L, gamma=0.0)
    removed = {0: np.array([0, 1])}
    res = unlearn(ckpt, removed, certificate_mode="none")
    assert res["abandonment_round"] == 0
    assert all(d["abandoned_this_round"] for d in res["diagnostics"])
