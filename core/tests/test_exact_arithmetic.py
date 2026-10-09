"""P0.3: fixed floating reduction order is not exact. The paper's own
adversarial case -- cached cell values 10**16, 1, -10**16, then delete the
record "1" -- must show ordinary float patching disagreeing with a fresh
reduction, and the exact accumulator agreeing with it exactly (bitwise,
never a tolerance check).
"""
from fixedpoint import FixedPointConfig, safe_chunk_size, sub_stats


def test_floating_patch_fails_the_cancellation_case():
    full = [10 ** 16, 1, -10 ** 16]
    deleted_value = 1
    retained = [10 ** 16, -10 ** 16]

    naive_float_full = 0.0
    for v in full:
        naive_float_full = naive_float_full + float(v)
    naive_float_patch = naive_float_full - float(deleted_value)

    fresh_float = 0.0
    for v in retained:
        fresh_float = fresh_float + float(v)

    # The point of the counterexample: patch-by-subtraction of a rounded
    # aggregate does not invert it -- the two do not agree.
    assert naive_float_patch != fresh_float
    assert naive_float_patch == -1.0
    assert fresh_float == 0.0


def test_exact_python_int_accumulation_passes_the_same_case():
    full = [10 ** 16, 1, -10 ** 16]
    deleted_value = 1
    retained = [10 ** 16, -10 ** 16]

    exact_patch = sum(full) - deleted_value  # Python bigint: never rounds
    exact_fresh = sum(retained)

    assert exact_patch == exact_fresh == 0


def test_sub_stats_reproduces_this_case_through_the_real_patch_code():
    # One (group=0, cluster=0) cell holding three 1-D points at these exact
    # grid values; verifies the module's own sub_stats, not hand arithmetic.
    N_full, S_full, SS_full = [[3]], [[[10 ** 16 + 1 + (-10 ** 16)]]], \
        [[10 ** 16 * 10 ** 16 + 1 * 1 + (-10 ** 16) * (-10 ** 16)]]
    N_del, S_del, SS_del = [[1]], [[[1]]], [[1]]

    N_p, S_p, SS_p = sub_stats((N_full, S_full, SS_full), (N_del, S_del, SS_del))

    N_fresh = [[2]]
    S_fresh = [[[10 ** 16 + (-10 ** 16)]]]
    SS_fresh = [[10 ** 16 * 10 ** 16 + (-10 ** 16) * (-10 ** 16)]]

    assert (N_p, S_p, SS_p) == (N_fresh, S_fresh, SS_fresh)


def test_chunk_size_is_int64_safe_at_realistic_feature_scale():
    """The written overflow proof, executable: for the declared fixed-point
    grid, no chunk's SS partial sum can approach int64's range."""
    cfg = FixedPointConfig(scale_bits=16, clip=8.0)
    for d in (1, 10, 100, 1000):
        chunk = safe_chunk_size(d, cfg.max_abs_int)
        per_point_worst_case = d * cfg.max_abs_int ** 2
        assert chunk >= 1
        assert chunk * per_point_worst_case < (1 << 63)
