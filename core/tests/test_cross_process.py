"""P0 appendix checklist item 9: fresh training and replay run as separate
top-level processes, never a coupled in-process oracle sharing arrays or
post-deletion labels. This is the only test in the suite that actually
launches two independent Python processes rather than two function calls
in the same interpreter.
"""
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np

from helpers import apply_removal, make_federation

HERE = Path(__file__).parent
SRC = str(HERE.parent / "src")
WORKER = str(HERE / "_cross_process_worker.py")


def _run_worker(mode, payload, tmp_path, tag):
    in_path = tmp_path / f"in_{tag}.pkl"
    out_path = tmp_path / f"out_{tag}.pkl"
    with open(in_path, "wb") as f:
        pickle.dump(payload, f)
    subprocess.run([sys.executable, WORKER, SRC, mode, str(in_path), str(out_path)], check=True)
    with open(out_path, "rb") as f:
        return pickle.load(f)


def test_fresh_and_replay_agree_across_separate_processes(tmp_path):
    client_data, group_of = make_federation(seed=41)
    seed, k, T, L, gamma = 41, 3, 3, 4, 0.0
    removed = {0: np.array([0, 1]), 3: np.array([0])}

    train_out = _run_worker("train", dict(client_data=client_data, group_of=group_of,
                                           seed=seed, k=k, T=T, L=L, gamma=gamma),
                             tmp_path, "orig")
    assert train_out["digests"]  # sanity: the training process actually ran

    cd_r, g_r = apply_removal(client_data, group_of, removed)
    fresh_out = _run_worker("train", dict(client_data=cd_r, group_of=g_r,
                                           seed=seed, k=k, T=T, L=L, gamma=gamma),
                             tmp_path, "fresh")

    checkpoint_path = tmp_path / "out_orig.pkl"
    replay_out = _run_worker("unlearn", dict(checkpoint_path=str(checkpoint_path),
                                              removed=removed, certificate_mode="runnerup"),
                              tmp_path, "replay")

    assert replay_out["digests"] == fresh_out["digests"]
    assert np.array_equal(replay_out["final_centers"], fresh_out["final_centers"])
