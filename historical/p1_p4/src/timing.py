"""Client/server timing accumulator shared by train.py and unlearn.py.

Every measured method (fresh training, direct replay, basic/runner-up
certified replay) fills the same buckets, so a caller can compare them
apples-to-apples and compute derived views the timers themselves take no
position on.

phase1_client is a per-client SCALAR (seconds): local seeding/rewind is a
one-shot step per client, run once, so the modeled parallel compute for Phase I is simply max() over clients -- no per-round
structure needed.

phase2_client_certify / phase2_client_recompute are per-client LISTS, one
entry per round: Phase II is iterative, and every client must finish round
t before the server can aggregate and start round t+1, so the realistic
wall-clock for Phase II is sum_t( max_c(certify[c][t] + recompute[c][t]) )
-- the per-ROUND slowest client, summed across rounds. A flat sum over
(client, round) instead answers a different question (total aggregate
compute-seconds across the whole client fleet, e.g. for a cost/energy
view) and is reported separately, never silently substituted for the
wall-clock number.

phase2_client_certify is the certificate-*checking* cost specifically,
separate from phase2_client_recompute (assignment/statistics work paid
whether or not certification was even attempted). It is all-zero for
methods that never certify (fresh training, direct replay).

phase1_server / phase2_server are single running totals: seeding the
compact server anchor set, combining clients' exact statistics, and the
center update all happen once, centrally -- there is no "parallel clients"
question on the server side.
"""
import time
from contextlib import contextmanager


def new_timing(client_ids, T: int) -> dict:
    client_ids = list(client_ids)
    return {
        "encoding": 0.0, "input_materialization": 0.0, "cache_construction": 0.0,
        "shift_bounds": 0.0, "fallback_sunk": 0.0, "fallback_rebuild": 0.0,
        "failed_assignment": 0.0, "certificate_scan": 0.0,
        "phase1_client": {c: 0.0 for c in client_ids},
        "phase1_server": 0.0,
        "phase2_client_certify": {c: [0.0] * T for c in client_ids},
        "phase2_client_recompute": {c: [0.0] * T for c in client_ids},
        "phase2_server": 0.0,
    }


@contextmanager
def add_to(bucket, key):
    """Times the enclosed block and adds the elapsed seconds to bucket[key].

    bucket may be: the top-level timing dict (key="phase1_server" or
    "phase2_server"), a per-client scalar dict (key=client id), or one
    client's per-round list (key=round index) -- `+=` at an index works
    the same way for a dict entry and a list entry, so one implementation
    covers all three call shapes.
    """
    t0 = time.perf_counter()
    yield
    bucket[key] += time.perf_counter() - t0


def totals(timing: dict) -> dict:
    """Derived summary. Two genuinely different "client time" numbers are
    both reported, explicitly labeled, rather than picking one silently:

    client_parallel_wall -- modeled federated compute critical path,
    assuming clients compute simultaneously with no stragglers/
    communication overhead: max-per-round summed over rounds (Phase II)
    plus max-over-clients (Phase I, one-shot).

    client_total_compute -- total CPU-seconds summed across every client
    and every round: a cost/energy-style aggregate, NOT a measured latency figure.
    Sum >= parallel-wall always, with equality only in the trivial C=1 case.
    """
    client_ids = list(timing["phase1_client"].keys())
    T = len(next(iter(timing["phase2_client_recompute"].values()))) if client_ids else 0

    phase1_parallel = max(timing["phase1_client"].values()) if client_ids else 0.0
    phase1_client_total = sum(timing["phase1_client"].values())

    phase2_parallel = 0.0
    certify_total = 0.0
    recompute_total = 0.0
    for t in range(T):
        round_max = 0.0
        for c in client_ids:
            cert_t = timing["phase2_client_certify"][c][t]
            rec_t = timing["phase2_client_recompute"][c][t]
            certify_total += cert_t
            recompute_total += rec_t
            round_max = max(round_max, cert_t + rec_t)
        phase2_parallel += round_max

    client_parallel_wall = phase1_parallel + phase2_parallel
    client_total_compute = phase1_client_total + certify_total + recompute_total
    server_total = timing["phase1_server"] + timing["phase2_server"]

    per_client_total = {
        c: (timing["phase1_client"][c] + sum(timing["phase2_client_certify"][c])
            + sum(timing["phase2_client_recompute"][c]))
        for c in client_ids
    }

    return dict(
        client_parallel_wall=client_parallel_wall,
        client_total_compute=client_total_compute,
        server_total=server_total,
        wall_total_parallel=client_parallel_wall + server_total,
        wall_total_compute=client_total_compute + server_total,
        certify_total=certify_total,
        recompute_total=recompute_total,
        phase1_client_parallel=phase1_parallel,
        phase1_client_total=phase1_client_total,
        phase1_server_total=timing["phase1_server"],
        phase2_server_total=timing["phase2_server"],
        per_client_total=per_client_total,
    )
