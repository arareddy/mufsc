"""Exact fixed-point feature encoding and additive sufficient statistics.

Fixed floating reduction order is not exact: in IEEE-754 double precision,
left-to-right summation of (1e16, 1, -1e16) gives 0, so deleting the record
`1` by aggregate subtraction gives -1, while a fresh reduction of the
retained records (1e16, -1e16) gives 0. Subtraction of a rounded sum does
not invert it.

We therefore (1) map every preprocessed coordinate onto a declared
fixed-point grid, m = round(clip(x) * 2**scale_bits), an exact integer, and
(2) accumulate the sufficient statistics N, S, SS as *exact* integers built
from these grid values, so that add/subtract/patch is always bit-identical
to a fresh reduction over the surviving index set, regardless of order.

Per-point coordinates and squared norms are accepted only after explicit
range validation against the declared int64-safe domain. The
cross-point accumulation does not: SS_{g,j} sums up to n*d point-coordinate
squares, which overflows int64 for realistic (n, d, scale_bits). Rather
than pick a bit width that happens to fit today's datasets, S and SS are
accumulated in chunks small enough to be provably int64-safe per chunk
(checked, not assumed), then combined across chunks as Python integers --
which have unbounded precision, so the combination itself can never
overflow. This is "another exact additive representation" in the sense of
the non-negotiable correctness conditions, not a fixed-width ring; it is
simpler to get right and never needs re-deriving for a new dataset scale.

N, S, SS are represented as (possibly nested) Python lists of Python ints
(never numpy int64) once returned from accumulate_stats, precisely so that
every downstream derived quantity (||S||^2, division by N, ...) is computed
in Python's arbitrary-precision or float arithmetic and can never silently
wrap. Only the hot per-chunk reduction touches numpy int64.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FixedPointConfig:
    scale_bits: int  # coordinates are multiples of 2**-scale_bits
    clip: float  # coordinates are clipped to [-clip, clip] before quantizing

    def __post_init__(self):
        if isinstance(self.scale_bits, (bool, np.bool_)) or not isinstance(self.scale_bits, (int, np.integer)) or not 0 <= self.scale_bits <= 30:
            raise ValueError("scale_bits must be an integer in 0..30")
        if not np.isfinite(self.clip) or self.clip <= 0 or self.clip * self.scale > 2**52:
            raise ValueError("invalid finite clip or encoded range")

    def validate_dimension(self, d):
        if not isinstance(d, (int, np.integer)) or not 1 <= d <= 4096:
            raise ValueError("dimension must be in 1..4096")
        safe_chunk_size(d, self.max_abs_int)

    @property
    def scale(self) -> int:
        return 1 << self.scale_bits

    @property
    def max_abs_int(self) -> int:
        """Largest magnitude a single quantized coordinate can take."""
        return int(round(self.clip * self.scale))


def quantize(X: np.ndarray, cfg: FixedPointConfig) -> np.ndarray:
    """Map standardized features onto the exact fixed-point grid (int64)."""
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError("features must be a finite 2D array")
    cfg.validate_dimension(X.shape[1])
    clipped = np.clip(X, -cfg.clip, cfg.clip)
    return np.round(clipped * cfg.scale).astype(np.int64)


def dequantize(X_int: np.ndarray, cfg: FixedPointConfig) -> np.ndarray:
    """Deterministic float64 view used for distances/assignment.

    Exactness of N,S,SS never depends on this function: it is only ever
    used for nearest-center computations with certified filters and exact
    rational fallback.
    """
    return X_int.astype(np.float64) / cfg.scale


def safe_chunk_size(d: int, max_abs_int: int, margin_bits: int = 4) -> int:
    """Largest number of points whose per-chunk SS partial sum is int64-safe.

    Worst case per point: d coordinates each at the maximal observed
    magnitude, so one point's squared-norm contribution is
    d * max_abs_int**2. margin_bits of headroom below 2**63 guards against
    the analysis being off by a small constant factor.
    """
    per_point_worst_case = d * (max_abs_int ** 2)
    budget = 1 << (63 - margin_bits)
    if d < 1 or max_abs_int < 0 or per_point_worst_case > budget:
        raise ValueError("unsafe per-point integer square range")
    return budget // max(per_point_worst_case, 1)


def _zeros_nested(shape) -> list:
    if len(shape) == 1:
        return [0] * shape[0]
    return [_zeros_nested(shape[1:]) for _ in range(shape[0])]


def _add_nested(acc: list, delta) -> None:
    """In-place acc += delta, where delta is a (possibly nested) int64 array."""
    if isinstance(delta, np.ndarray) and delta.ndim > 1:
        for a_row, d_row in zip(acc, delta):
            _add_nested(a_row, d_row)
    else:
        for i, v in enumerate(delta):
            acc[i] += int(v)


def accumulate_stats(X_int: np.ndarray, group_idx: np.ndarray, labels: np.ndarray,
                      num_groups: int, k: int) -> tuple:
    """Exact N, S, SS over (group, cluster) cells, chunked for safety.

    X_int: (n, d) int64 quantized points.
    group_idx: (n,) int in [0, num_groups) -- which group each point belongs to.
    labels: (n,) int in [0, k) -- which cluster each point is assigned to.

    Returns (N, S, SS) as nested Python-int lists of shape (num_groups, k),
    (num_groups, k, d), (num_groups, k) respectively. N is exact trivially
    (counts never approach int64 range); S and SS are exact by the chunked
    accumulation described in the module docstring.
    """
    X_int = np.asarray(X_int)
    if X_int.ndim != 2 or X_int.dtype != np.int64:
        raise ValueError("encoded features must be an int64 matrix")
    n, d = X_int.shape
    group_idx, labels = np.asarray(group_idx), np.asarray(labels)
    if num_groups < 1 or k < 1 or group_idx.shape != (n,) or labels.shape != (n,):
        raise ValueError("invalid accumulator dimensions")
    for ids, bound in ((group_idx, num_groups), (labels, k)):
        if not np.issubdtype(ids.dtype, np.integer) or np.any(ids < 0) or np.any(ids >= bound):
            raise ValueError("invalid accumulator IDs")
    if X_int.size and np.any(X_int == np.iinfo(np.int64).min):
        raise ValueError("unsafe int64 minimum")
    max_abs_int = int(np.max(np.abs(X_int))) if X_int.size else 0
    chunk = safe_chunk_size(d, max_abs_int)
    N = _zeros_nested((num_groups, k))
    S = _zeros_nested((num_groups, k, d))
    SS = _zeros_nested((num_groups, k))

    sq_norms = np.sum(X_int.astype(np.int64) ** 2, axis=1, dtype=np.int64)

    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        g_c, l_c = group_idx[start:end], labels[start:end]
        x_c = X_int[start:end]
        sq_c = sq_norms[start:end]

        n_part = np.zeros((num_groups, k), dtype=np.int64)
        np.add.at(n_part, (g_c, l_c), 1)
        _add_nested(N, n_part)

        s_part = np.zeros((num_groups, k, d), dtype=np.int64)
        np.add.at(s_part, (g_c, l_c), x_c)
        _add_nested(S, s_part)

        ss_part = np.zeros((num_groups, k), dtype=np.int64)
        np.add.at(ss_part, (g_c, l_c), sq_c)
        _add_nested(SS, ss_part)

    return N, S, SS


def new_zero_stats(num_groups: int, k: int, d: int) -> tuple:
    return _zeros_nested((num_groups, k)), _zeros_nested((num_groups, k, d)), _zeros_nested((num_groups, k))


def add_stats(a: tuple, b: tuple) -> tuple:
    """Exact elementwise a + b for two (N, S, SS) triples."""
    return (_elementwise(a[0], b[0], lambda x, y: x + y),
            _elementwise(a[1], b[1], lambda x, y: x + y),
            _elementwise(a[2], b[2], lambda x, y: x + y))


def sub_stats(a: tuple, b: tuple) -> tuple:
    """Exact elementwise a - b for two (N, S, SS) triples."""
    return (_elementwise(a[0], b[0], lambda x, y: x - y),
            _elementwise(a[1], b[1], lambda x, y: x - y),
            _elementwise(a[2], b[2], lambda x, y: x - y))


def _elementwise(a, b, op):
    if isinstance(a, list) and a and isinstance(a[0], list):
        return [_elementwise(x, y, op) for x, y in zip(a, b)]
    return [op(x, y) for x, y in zip(a, b)]


def exact_squared_norm(vec) -> int:
    """||vec||^2 for a Python-int vector, computed with unbounded precision."""
    return sum(int(v) * int(v) for v in vec)


def represented_clients(client_data, cfg):
    """Materialize one fine-grid dataset for every phase and reported quality."""
    encoded = {c: quantize(x, cfg) for c, x in sorted(client_data.items())}
    return {c: dequantize(x, cfg) for c, x in encoded.items()}, encoded
