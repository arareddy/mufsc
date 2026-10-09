"""P0: certificate soundness and separation, using the paper's own numeric
examples verbatim (appendix, "Assignment Certificates"). Without these, the
runner-up certificate's distinguishing logic -- the exact-norm |d2-delta_r|
branch and the top-3 exclusion term -- is never exercised: every other test
in this suite happens to have basic and runner-up agree.
"""
import numpy as np

from certificates import basic_certificate, runner_up_certificate


def test_runner_up_strictly_improves_on_basic_at_k_equals_2():
    """d1=0, d2=1, delta_j=0, delta_r=100: basic must reject (the shift
    bound alone looks unsafe), runner-up must accept (the competitor's
    *exact*-norm reverse-triangle bound puts it at distance >= 99)."""
    d1, d2 = 0.0, 1.0
    delta = np.array([0.0, 100.0])
    j, r = 0, 1

    assert not basic_certificate(d1, d2, delta, j)
    assert runner_up_certificate(d1, d2, delta, j, r)


def test_runner_up_only_without_exclusion_term_would_be_unsound():
    """Winner at 0, runner-up at 10, a third center at 11, x=0. Winner moves
    to 0.5, runner-up stays at 10, third moves to 0.1 -- the third center
    becomes the true nearest, so any certificate ignoring it is unsound. A
    runner-up-only test (no exclusion term) would wrongly accept; the full
    certificate (which folds in the largest non-runner shift) must reject.
    """
    d1, d2 = 0.0, 10.0
    delta = np.array([0.5, 0.0, 10.9])  # [winner, runner-up, third]
    j, r = 0, 1

    naive_runner_up_only = (d1 + delta[j]) < abs(d2 - delta[r])
    assert naive_runner_up_only  # the unsound simplification would accept

    assert not runner_up_certificate(d1, d2, delta, j, r)  # the real one rejects

    # Ground truth: the third center really is nearest after the shift.
    true_d_winner = abs(0.0 - 0.5)
    true_d_third = abs(0.0 - 0.1)
    assert true_d_third < true_d_winner


def test_basic_certificate_uses_the_max_over_every_competitor():
    """A shared update scalar can move every center at once; comparing only
    against the cached runner-up's own shift (ignoring a bigger mover
    elsewhere) is exactly the bug an earlier version of this algorithm
    shipped with."""
    d1, d2 = 0.0, 1.0
    j = 0
    delta_small_other_mover = np.array([0.0, 0.4, 0.0])  # max_{m!=j} = 0.4 < margin=1: passes
    delta_big_other_mover = np.array([0.0, 0.4, 1.05])  # max_{m!=j} = 1.05 >= margin=1: fails

    assert basic_certificate(d1, d2, delta_small_other_mover, j)
    assert not basic_certificate(d1, d2, delta_big_other_mover, j)
