"""Saved numeric evidence from independently launched training and replay."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(os.environ.get("FTF_ORACLE_PROCESS_EVIDENCE",
                str(ROOT / "remediation" / "evidence" / "oracle" / "processes")))
WORKER = Path(__file__).with_name("process_worker.py")


def cases():
    result = []
    for bits, L in [(12, 6), (16, 20)]:
        for seed in [0, 1, 19]:
            rng = np.random.default_rng(17 + seed)
            data = {str(c): (rng.integers(-100, 100, (9 + offset, 3)) / 29).tolist()
                    for offset, c in enumerate([2, 9, 17])}
            groups = {str(c): [i % 2 for i in range(9 + offset)] for offset, c in enumerate([2, 9, 17])}
            result.append({"name": f"mixed_b{bits}_L{L}_s{seed}", "data": data, "groups": groups,
                           "removed": {"2": [3, 0], "17": [2]}, "parameters":
                           {"seed": seed, "k": 3, "T": 4, "L": L, "bits": bits, "clip": 8.,
                            "gamma": .2 if seed == 1 else 0., "anchor_lloyd_iters": 1 if seed == 19 else 0}})
        result.append({"name": f"old_underflow_b{bits}",
                       "data": {"0": [[1e-150], [np.nextafter(1e-150, np.inf)], [1e-150]],
                                "1": [[np.nextafter(1e-150, np.inf)], [1e-150], [np.nextafter(1e-150, np.inf)]]},
                       "groups": {"0": [0, 0, 0], "1": [1, 1, 1]}, "removed": {"0": [0]},
                       "parameters": {"seed": 1, "k": 2, "T": 3, "L": L, "bits": bits, "clip": 8.}})
        result.append({"name": f"empty_client_and_saturation_b{bits}",
                       "data": {"0": [[1.]], "3": [[2.], [3.]], "9": [[4.], [5.]]},
                       "groups": {"0": [0], "3": [0, 0], "9": [1, 1]}, "removed": {"0": [0], "9": [1]},
                       "parameters": {"seed": 3, "k": 6, "T": 3, "L": L, "bits": bits, "clip": 8.}})
        result.append({"name": f"stable_nonempty_deletion_b{bits}",
                       "data": {"0": [[0.], [0.], [0.]], "1": [[4.], [4.], [4.]]},
                       "groups": {"0": [0, 0, 0], "1": [1, 1, 1]}, "removed": {"0": [0]},
                       "parameters": {"seed": 31, "k": 2, "T": 5, "L": L, "bits": bits, "clip": 8.}})
        result.append({"name": f"no_deletion_k1_b{bits}",
                       "data": {"2": [[1 / 3], [2.], [3.]], "6": [[1 / 3], [4.], [5.]]},
                       "groups": {"2": [0, 1, 0], "6": [1, 0, 1]}, "removed": {},
                       "parameters": {"seed": 7, "k": 1, "T": 3, "L": L, "bits": bits, "clip": 8.}})
    return result


@pytest.mark.parametrize("case", cases(), ids=lambda case: case["name"])
def test_fresh_and_every_replay_match_independent_oracle_across_processes(case):
    directory = EVIDENCE / case["name"]
    directory.mkdir(parents=True, exist_ok=True)
    source, checkpoint = directory / "case.json", directory / "checkpoint.pkl"
    source.write_text(json.dumps(case, indent=2) + "\n")
    results = {}
    for index, mode in enumerate(["checkpoint", "oracle", "fresh", "none", "basic", "runnerup"]):
        output = directory / f"{mode}.json"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED=str(103 + index * 97),
                   OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        execution = subprocess.run([sys.executable, str(WORKER), "--case", str(source), "--mode", mode,
                                    "--checkpoint", str(checkpoint), "--output", str(output)],
                                   env=env, text=True, capture_output=True)
        (directory / f"{mode}.log").write_text(execution.stdout + execution.stderr)
        assert execution.returncode == 0, execution.stderr
        results[mode] = json.loads(output.read_text())
    pids = [r["process"]["pid"] for r in results.values()]
    assert len(set(pids)) == len(pids)
    oracle = results["oracle"]
    for mode in ["fresh", "none", "basic", "runnerup"]:
        actual = results[mode]
        # Exact serialized indexed coordinates and complete integers, no tolerance,
        # no permutation matching, and no reliance on production digest flags.
        assert actual["trajectory"] == oracle["trajectory"], f"{case['name']} {mode} trajectory"
        assert actual["per_round_stats"] == oracle["per_round_stats"], f"{case['name']} {mode} N/S/SS"
        assert actual["slices"] == oracle["slices"], f"{case['name']} {mode} local selected IDs/masses"
    assert results["fresh"]["cache_valid"] is True
    assert all(results[mode]["cache_valid"] is False for mode in ["none", "basic", "runnerup"])
    if case["name"].startswith("stable_"):
        for mode in ["basic", "runnerup"]:
            assert all(row["S"] == 5 for row in results[mode]["diagnostics"])
