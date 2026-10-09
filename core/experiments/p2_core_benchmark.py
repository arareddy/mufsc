"""P2: the revised 175-trial core benchmark (EXPERIMENT_EXECUTION_PLAN.md
P2 / appendix Experiment 1), rerun under the declared SplitGroup-2k +
GuardedFairUpdate + exact-accumulator map -- the earlier merged-summary/
dense-expansion numbers are explicitly excluded by the paper itself and are
not reused here.

Configurations (record counts match the appendix's Experiment-1 table once
the file's larger client pool is subsampled to these counts, without
resampling within a client):
    Adult:  100 clients, k in 4..16,                              5 trials each -> 65
    Bank:    20 clients, k in {2,3,4,5,10,20,30,40,50},            5 trials each -> 45
    Credit: 100 clients, k in 4..16,                               5 trials each -> 65
Total 175 trials, each producing 4 measured methods (fresh retraining,
direct full replay, basic CertifiedReplay, runner-up CertifiedReplay) run
through the identical exact-accumulator kernels -- "apply every
optimization symmetrically" (appendix, "Required baselines and symmetry
rules"): the same train_full()/unlearn() code paths serve all four.

Each trial: (1) train once on the full client set -- this is the
checkpoint being unlearned, not itself a measured baseline; (2) sample and
archive a deletion batch *before* running anything; (3) fresh-retrain on
the retained data (measured); (4) unlearn the step-1 checkpoint in each of
the three replay modes (measured); (5) check every replay's digests match
fresh's digests exactly -- no permutation matching, no tolerance.

Client/server timing (added per review, on top of the original
wall-clock-only pass -- see src/timing.py for the full accounting):
  - train.py/unlearn.py split every second into phase1_client (each
    client's own seeding/rewind work, a one-shot step), phase1_server (the
    always-rerun compact server reseed), phase2_client_certify (the
    certificate CHECK itself, per round, zero for fresh/direct which never
    certify), phase2_client_recompute (per-round assignment + statistics
    work, paid regardless of certification), and phase2_server (per round:
    combining clients' exact deltas + the center update).
  - speedup_wall is the original single measured-process wall-clock
    speedup (this script runs every client sequentially in one process, so
    it is neither a pure parallel-deployment number nor a pure aggregate-
    cost number -- just what this run actually took).
  - client_parallel_wall_seconds is the metric that matters for "how fast
    would a real federated deployment be": Phase I is one-shot, so it's
    max() over clients; Phase II is iterative and every client must finish
    round t before the server aggregates and starts round t+1, so it's
    sum over rounds of max-over-clients-in-that-round. speedup_client_
    parallel is fresh/method on this number -- assumes an infinitely fast
    server, real parallel clients, no stragglers or communication delay.
  - client_total_compute_seconds sums every client's time across the
    WHOLE fleet instead of taking the per-round max -- a total CPU-seconds
    / cost-and-energy view, not a latency one. speedup_client_compute is
    fresh/method on this number. client_total_compute_seconds is always
    >= client_parallel_wall_seconds (sum of nonnegative numbers >= their
    max), so speedup_client_compute and speedup_client_parallel are
    genuinely different numbers, not two labels for the same one --
    reporting both, clearly labeled, rather than picking one, is the
    point; conflating them was an error in the first version of this
    measurement.
  - certify_seconds isolates certificate-checking cost specifically, so
    "is certification worth its own overhead" is a number, not an
    inference from the fact that certified ended up slower than direct.
  - client_speedup_{mean,median,max,min} is the *per-client* speedup
    distribution (each client's own fresh-time / its own method-time,
    using each client's own total across all rounds) -- "local unlearning
    efficiency at the client level", not one trial-wide average a few
    heavily-touched clients could dominate.
"""
import argparse
import csv
import hashlib
import os
import pickle
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datasets import load_dataset  # noqa: E402
from fixedpoint import FixedPointConfig  # noqa: E402
from objective import fair_objective  # noqa: E402
from timing import totals  # noqa: E402
from train import train_full  # noqa: E402
from unlearn import unlearn  # noqa: E402

T_ROUNDS = 15
L_BISECTION = 6
SCALE_BITS = 12
N_TRIALS = 5
DELETION_FRAC = 0.001  # of the TOTAL pooled dataset, drawn globally (not per-client)
DELETION_MIN = 20

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
ARCHIVE_DIR = os.path.join(RESULTS_DIR, "p2_deletion_archive")

DATASET_K_GRIDS = {
    "adult": list(range(4, 17)),
    "bank": [2, 3, 4, 5, 10, 20, 30, 40, 50],
    "credit": list(range(4, 17)),
}


def sample_removal(client_data: dict, group_of: dict, seed: int, frac: float) -> dict:
    """A small batch drawn uniformly at random from the *pooled* dataset,
    not per-client-proportionally: with C ~= 20-100 small clients, a
    per-client-proportional draw touches every client a little (and
    everyone's Phase-I anchors with it), which is a legitimate stress
    regime (that's what P6, deletion concentration, is for) but not a
    realistic "someone asked for their few records back" request, and it
    silently forces abandonment on every trial regardless of certificate
    quality -- burying exactly the effect this benchmark exists to show.
    A global uniform draw instead touches a random handful of clients and
    leaves the rest -- and most individual assignments -- untouched,
    matching a single ordinary deletion request. Broader/targeted regimes
    belong to the later deletion-stress experiment, not this one.
    Never empties a global group (checked below; resample on violation).
    """
    n_total = sum(X.shape[0] for X in client_data.values())
    r = max(DELETION_MIN, int(round(n_total * frac)))
    client_ids = sorted(client_data.keys())
    sizes = np.array([client_data[c].shape[0] for c in client_ids])
    offsets = np.concatenate([[0], np.cumsum(sizes)])

    rng = np.random.default_rng(seed)
    for attempt in range(10):
        flat_idx = rng.choice(n_total, size=min(r, n_total - 1), replace=False)
        removed = {c: [] for c in client_ids}
        for fi in flat_idx:
            ci = int(np.searchsorted(offsets, fi, side="right") - 1)
            removed[client_ids[ci]].append(int(fi - offsets[ci]))
        removed = {c: np.sort(np.array(v, dtype=np.int64)) for c, v in removed.items() if v}
        if _removal_is_valid(client_data, group_of, removed):
            return removed
        seed += 1_000_003  # resample deterministically rather than looping the same draw
    raise RuntimeError("could not sample a valid removal after 10 attempts")


def _removal_is_valid(client_data, group_of, removed):
    for g in (0, 1):
        retained = sum(int(np.sum((group_of[c] == g) &
                                   _retained_mask(X_c, removed.get(c, np.array([], dtype=np.int64)))))
                       for c, X_c in client_data.items())
        if retained == 0:
            return False
    return True


def _retained_mask(X_c, removed_c):
    mask = np.ones(X_c.shape[0], dtype=bool)
    mask[removed_c] = False
    return mask


def apply_removal(client_data: dict, group_of: dict, removed: dict) -> tuple:
    new_cd, new_g = {}, {}
    for c, X_c in client_data.items():
        mask = _retained_mask(X_c, removed.get(c, np.array([], dtype=np.int64)))
        new_cd[c] = X_c[mask]
        new_g[c] = group_of[c][mask]
    return new_cd, new_g


def removal_hash(removed: dict) -> str:
    h = hashlib.sha256()
    for c in sorted(removed):
        h.update(str(c).encode())
        h.update(removed[c].tobytes())
    return h.hexdigest()[:16]


def run_trial(dataset_name, client_data, group_of, fp_cfg, k, trial_idx, seed, rows):
    removed = sample_removal(client_data, group_of, seed + 500_000, DELETION_FRAC)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archive_path = os.path.join(ARCHIVE_DIR, f"{dataset_name}_k{k}_t{trial_idx}_seed{seed}.pkl")
    with open(archive_path, "wb") as f:
        pickle.dump({"seed": seed, "removed": removed}, f)

    t0 = time.perf_counter()
    ckpt = train_full(client_data, group_of, seed, k, T_ROUNDS, L_BISECTION, gamma=0.0, fp_cfg=fp_cfg)
    t_setup = time.perf_counter() - t0

    cd_r, g_r = apply_removal(client_data, group_of, removed)

    t0 = time.perf_counter()
    fresh = train_full(cd_r, g_r, seed, k, T_ROUNDS, L_BISECTION, gamma=0.0, fp_cfg=fp_cfg)
    t_fresh = time.perf_counter() - t0
    fresh_t = totals(fresh["timing"])
    X_r = np.concatenate([cd_r[c] for c in sorted(cd_r)], axis=0)
    g_r_flat = np.concatenate([g_r[c] for c in sorted(g_r)], axis=0)
    phi_a, phi_b, G, Phi = fair_objective(X_r, g_r_flat, fresh["final_centers"])

    common = dict(dataset=dataset_name, k=k, trial=trial_idx, seed=seed,
                  n=sum(X.shape[0] for X in client_data.values()), C=len(client_data),
                  d=next(iter(client_data.values())).shape[1],
                  T=T_ROUNDS, L=L_BISECTION, clip=fp_cfg.clip, scale_bits=fp_cfg.scale_bits,
                  removal_size=sum(len(v) for v in removed.values()),
                  removal_hash=removal_hash(removed), setup_train_seconds=t_setup)

    rows.append(dict(common, method="fresh_retraining", elapsed_seconds=t_fresh,
                      digest_match=True, max_center_dev=0.0,
                      speedup_wall=1.0, speedup_client_parallel=1.0, speedup_client_compute=1.0,
                      client_parallel_wall_seconds=fresh_t["client_parallel_wall"],
                      client_total_compute_seconds=fresh_t["client_total_compute"],
                      server_total_seconds=fresh_t["server_total"],
                      certify_seconds=fresh_t["certify_total"],
                      phase1_client_parallel_seconds=fresh_t["phase1_client_parallel"],
                      phase1_server_seconds=fresh_t["phase1_server_total"],
                      phase2_server_seconds=fresh_t["phase2_server_total"],
                      **{f"client_speedup_{k2}": 1.0 for k2 in ("mean", "median", "max", "min")},
                      abandonment_round="", final_G=G, final_Phi=Phi,
                      final_Phi_A=phi_a, final_Phi_B=phi_b))

    for mode, label in (("none", "direct_full_replay"), ("basic", "certified_basic"),
                        ("runnerup", "certified_runnerup")):
        t0 = time.perf_counter()
        res = unlearn(ckpt, removed, certificate_mode=mode)
        elapsed = time.perf_counter() - t0
        res_t = totals(res["timing"])
        digest_match = res["digests"] == fresh["digests"]
        max_dev = float(np.max(np.abs(res["final_centers"] - fresh["final_centers"])))
        phi_a2, phi_b2, G2, Phi2 = fair_objective(X_r, g_r_flat, res["final_centers"])
        cs = client_speedup_stats(fresh_t["per_client_total"], res_t["per_client_total"])
        rows.append(dict(
            common, method=label, elapsed_seconds=elapsed,
            digest_match=digest_match, max_center_dev=max_dev,
            speedup_wall=(t_fresh / elapsed if elapsed > 0 else float("inf")),
            speedup_client_parallel=(fresh_t["client_parallel_wall"] / res_t["client_parallel_wall"]
                                      if res_t["client_parallel_wall"] > 0 else float("inf")),
            speedup_client_compute=(fresh_t["client_total_compute"] / res_t["client_total_compute"]
                                     if res_t["client_total_compute"] > 0 else float("inf")),
            client_parallel_wall_seconds=res_t["client_parallel_wall"],
            client_total_compute_seconds=res_t["client_total_compute"],
            server_total_seconds=res_t["server_total"],
            certify_seconds=res_t["certify_total"],
            phase1_client_parallel_seconds=res_t["phase1_client_parallel"],
            phase1_server_seconds=res_t["phase1_server_total"],
            phase2_server_seconds=res_t["phase2_server_total"],
            client_speedup_mean=cs["mean"], client_speedup_median=cs["median"],
            client_speedup_max=cs["max"], client_speedup_min=cs["min"],
            abandonment_round=res["abandonment_round"],
            final_G=G2, final_Phi=Phi2, final_Phi_A=phi_a2, final_Phi_B=phi_b2))
        if not digest_match:
            print(f"  !! EXACTNESS FAILURE dataset={dataset_name} k={k} trial={trial_idx} "
                  f"method={label} max_dev={max_dev:.3e}", flush=True)


def client_speedup_stats(fresh_per_client: dict, method_per_client: dict, eps: float = 1e-9) -> dict:
    """Per-client speedup distribution (ask: 'local unlearning efficiency
    at client level'). Each client's own fresh-retrain time is compared to
    its own time under this method -- a client whose slice was never
    touched and every point stayed certified pays close to zero, giving a
    very large but finite ratio (eps floor avoids a literal division by
    zero rather than reporting inf, which is awkward to aggregate)."""
    fresh_vals = np.array([fresh_per_client[c] for c in fresh_per_client])
    method_vals = np.array([method_per_client.get(c, 0.0) for c in fresh_per_client])
    ratios = fresh_vals / np.maximum(method_vals, eps)
    return dict(mean=float(np.mean(ratios)), median=float(np.median(ratios)),
                max=float(np.max(ratios)), min=float(np.min(ratios)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", type=str, default="adult,bank,credit")
    ap.add_argument("--quick", action="store_true", help="one k-value, one trial per dataset (smoke test)")
    ap.add_argument("--data-dir", type=str, default=os.path.join(
        os.path.dirname(__file__), "..", "..", "v0", "data"))
    ap.add_argument("--out", type=str, default=os.path.join(RESULTS_DIR, "p2_core_benchmark.csv"))
    args = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    wanted = args.datasets.split(",")
    rows = []
    t_start = time.time()

    for name in wanted:
        client_data, group_of, meta = load_dataset(name, args.data_dir, seed=0)
        fp_cfg = FixedPointConfig(scale_bits=SCALE_BITS, clip=meta["clip"])
        print(f"[{name}] loaded: C={meta['num_clients']} n={meta['n_total']} d={meta['d']} clip={meta['clip']}",
              flush=True)

        k_grid = DATASET_K_GRIDS[name]
        if args.quick:
            k_grid = k_grid[:1]
        n_trials = 1 if args.quick else N_TRIALS

        for k in k_grid:
            for trial_idx in range(n_trials):
                seed = k * 1000 + trial_idx
                t0 = time.time()
                run_trial(name, client_data, group_of, fp_cfg, k, trial_idx, seed, rows)
                print(f"[{name}] k={k:3d} trial={trial_idx} done in {time.time()-t0:.1f}s "
                      f"(total elapsed {time.time()-t_start:.1f}s)", flush=True)
                with open(args.out, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)

    n_fail = sum(1 for r in rows if r["method"] != "fresh_retraining" and not r["digest_match"])
    print(f"\nDONE. {len(rows)} rows written to {args.out}. "
          f"Exactness failures: {n_fail}/{sum(1 for r in rows if r['method']!='fresh_retraining')}")


if __name__ == "__main__":
    raise SystemExit("Reference helper driver only. Execute corrected gated runs with: python remediation/scripts/run_experiments.py --stages P2 --run-id corrected-v1")
