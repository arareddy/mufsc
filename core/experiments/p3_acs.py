#!/usr/bin/env python3
"""P3: ACS/Folktables natural-federation experiment.

This is intentionally the only P3 source file.  It prepares the frozen ACS
federations and calls the repository's existing ``train_full`` and ``unlearn``
kernels; it does not contain another Fair-to-Forget implementation.

Commands are separated so aggregation, plotting, compact-table generation,
and report generation consume saved CSV files and never retrain a model.
All generated artifacts live below ``rtesults/`` (spelling requested by the
user).
"""

from __future__ import annotations

# Freeze the runtime symmetry declaration before NumPy or a BLAS backend is
# imported.  All four measured methods run in this same single-thread process.
import os

for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_thread_variable] = "1"

import argparse
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import gc
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPOSITORY_ROOT.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import modules, rather than copying their functions, so the light-weight
# communication counter can observe the existing logical client-summary calls.
import train as baseline_train  # noqa: E402
import unlearn as baseline_unlearn  # noqa: E402
from fixedpoint import FixedPointConfig  # noqa: E402


# ---------------------------------------------------------------------------
# Frozen declaration -- selected before this P3 run and never inferred from a
# clustering, fairness, deletion, margin, certificate, runtime, or communication
# result.
# ---------------------------------------------------------------------------

STATE_FIPS = OrderedDict(
    (
        ("AL", 1), ("AK", 2), ("AZ", 4), ("AR", 5), ("CA", 6),
        ("CO", 8), ("CT", 9), ("DE", 10), ("FL", 12), ("GA", 13),
        ("HI", 15), ("ID", 16), ("IL", 17), ("IN", 18), ("IA", 19),
        ("KS", 20), ("KY", 21), ("LA", 22), ("ME", 23), ("MD", 24),
        ("MA", 25), ("MI", 26), ("MN", 27), ("MS", 28), ("MO", 29),
        ("MT", 30), ("NE", 31), ("NV", 32), ("NH", 33), ("NJ", 34),
        ("NM", 35), ("NY", 36), ("NC", 37), ("ND", 38), ("OH", 39),
        ("OK", 40), ("OR", 41), ("PA", 42), ("RI", 44), ("SC", 45),
        ("SD", 46), ("TN", 47), ("TX", 48), ("UT", 49), ("VT", 50),
        ("VA", 51), ("WA", 53), ("WV", 54), ("WI", 55), ("WY", 56),
    )
)

FEATURE_NAMES = (
    "AGEP", "SCHL", "MAR", "RELP", "DIS", "ESP", "CIT", "MIG",
    "MIL", "ANC", "NATIVITY", "DEAR", "DEYE", "DREM", "SEX", "RAC1P",
)
CONTINUOUS_FEATURES = ("AGEP",)
CATEGORICAL_FEATURES = tuple(name for name in FEATURE_NAMES if name != "AGEP")

N_GRID = (100_000, 250_000, 500_000, 1_000_000)
C_GRID = (10, 25, 50, 100, 250)
K_GRID = (4, 8, 16, 32, 64)
T_GRID = (5, 10, 20, 40)
DELETION_FRACTION_GRID = (
    Decimal("0.00001"), Decimal("0.0001"), Decimal("0.001"),
    Decimal("0.01"), Decimal("0.05"),
)
MASTER_SEEDS = (0, 1, 2, 3, 4)

CLIENT_SELECTION_SEED = 0
RECORD_SUBSAMPLING_SEED = 1
DELETION_SAMPLING_SEED = 2
NEARLY_PURE_THRESHOLD = 0.95

L_BISECTION = 6
GAMMA = 0.0
SCALE_BITS = 12
ANCHOR_LLOYD_ITERS = 0
ABANDON_THRESHOLD = 0.5

# The inexpensive reference makes the required 19-run saturated design
# practical while retaining every requested factor level.
REFERENCE = (100_000, 50, 4, 5, Decimal("0.001"))

METHODS = OrderedDict(
    (
        ("Fresh Retraining", "fresh"),
        ("Direct Full Replay", "none"),
        ("Basic All-Competitor CertifiedReplay", "basic"),
        ("Runner-Up-Identity CertifiedReplay", "runnerup"),
    )
)
CERTIFICATE_LABELS = OrderedDict(
    (
        ("Basic All-Competitor CertifiedReplay", "Basic All-Competitor Certificate"),
        ("Runner-Up-Identity CertifiedReplay", "Runner-Up-Identity Certificate"),
    )
)

MISSING_VALUE_RULE = (
    "Apply the Folktables ACSEmployment task preprocessing (identity); retain "
    "records with nonmissing positive PUMA and SEX code 1 or 2; replace each "
    "remaining feature NaN with numeric sentinel -1; reject any remaining infinity"
)
CATEGORICAL_ENCODING_RULE = (
    "Retain every ACS PUMS categorical integer code as one numeric coordinate; "
    "do not one-hot expand or learn an ordering transformation"
)
STANDARDIZATION_RULE = (
    "For every coordinate, subtract the float64 mean and divide by the population "
    "standard deviation (ddof=0) of the complete eligible 2018 1-Year 50-state "
    "pool before client selection or record subsampling; replace zero std by 1"
)
GROUP_RULE = "Group A is SEX code 1; Group B is SEX code 2"
CLIENT_SELECTION_RULE = (
    "Sort the complete eligible natural-client pool by identifier, apply one fixed "
    "NumPy SeedSequence permutation using client-selection seed 0 and a distinct "
    "state/PUMA role, then take prefixes (states for C=10,25,50; complete "
    "state-plus-PUMA identifiers for C=100,250)"
)
RECORD_SUBSAMPLING_RULE = (
    "Allocate n proportionally to eligible client counts by exact integer "
    "largest-remainder rounding (ties by prefix position), then sample each quota "
    "without replacement using deterministic geography-keyed streams derived from "
    "record-subsampling seed 1; no demographic stratification"
)
DELETION_SAMPLING_RULE = (
    "For each (n,C,k,T,requested fraction,master seed), draw exactly r pooled "
    "records uniformly without replacement from its clean checkpoint using a "
    "deterministic stream derived from deletion-sampling base seed 2; requests are "
    "independent and noncumulative"
)
COMMUNICATION_RULE = (
    "The baseline has no network-byte meter. P3 minimally counts numeric scalars "
    "in client-to-server payloads already materialized by its existing calls: each "
    "SplitGroup slice call contributes k_e*(d+1) anchor-coordinate/multiplicity "
    "scalars and each exact (N,S,SS) accumulation call contributes 2*k*(d+2) "
    "scalars. It is an application-payload counter, not serialized/network bytes."
)

DECLARATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment": "P3. ACS/Folktables Natural Federation",
    "acs_task": "ACSEmployment",
    "acs_survey_year": 2018,
    "acs_horizon": "1-Year",
    "acs_survey": "person",
    "geographic_filters": {
        "states": list(STATE_FIPS),
        "excluded": ["District of Columbia", "Puerto Rico"],
        "pumas": "all nonmissing positive PUMAs within the fixed 50-state filter",
    },
    "feature_columns": list(FEATURE_NAMES),
    "continuous_features": list(CONTINUOUS_FEATURES),
    "categorical_features": list(CATEGORICAL_FEATURES),
    "missing_value_rule": MISSING_VALUE_RULE,
    "categorical_encoding_rule": CATEGORICAL_ENCODING_RULE,
    "standardization_rule": STANDARDIZATION_RULE,
    "two_group_definition": GROUP_RULE,
    "natural_client_selection_rule": CLIENT_SELECTION_RULE,
    "natural_client_selection_seed": CLIENT_SELECTION_SEED,
    "record_subsampling_rule": RECORD_SUBSAMPLING_RULE,
    "record_subsampling_seed": RECORD_SUBSAMPLING_SEED,
    "deletion_sampling_rule": DELETION_SAMPLING_RULE,
    "deletion_sampling_seed": DELETION_SAMPLING_SEED,
    "nearly_pure_threshold": NEARLY_PURE_THRESHOLD,
    "nearly_pure_rule": (
        "not strictly pure and max(group-A proportion, group-B proportion) >= 0.95"
    ),
    "kappa_rule": (
        "max(1, max over mixed clients of max(a_c/b_c,b_c/a_c)), where "
        "a_c=n_cA/n_A and b_c=n_cB/n_B; pure clients contribute factor 1"
    ),
    "touched_slice_mass_rule": (
        "M_s=sum of retained sizes of exactly the touched pseudo-slices e=(c,g)"
    ),
    "margin_rule": "cached certificate margin m_t(x)=d2_t(x)-d1_t(x)",
    "communication_rule": COMMUNICATION_RULE,
    "algorithm": {
        "L_bisection": L_BISECTION,
        "gamma": GAMMA,
        "fixed_point_scale_bits": SCALE_BITS,
        "fixed_point_clip_rule": "ceil(max absolute standardized pool value)+1",
        "anchor_lloyd_iters": ANCHOR_LLOYD_ITERS,
        "certificate_abandon_threshold": ABANDON_THRESHOLD,
    },
    "grids": {
        "n": list(N_GRID), "C": list(C_GRID), "k": list(K_GRID),
        "T": list(T_GRID),
        "deletion_fraction": [format(value, "f") for value in DELETION_FRACTION_GRID],
    },
    "fractional_design": {
        "type": "reference plus one-factor sweeps",
        "reference": [
            REFERENCE[0], REFERENCE[1], REFERENCE[2], REFERENCE[3],
            format(REFERENCE[4], "f"),
        ],
        "requested_configurations": 19,
        "reason": (
            "Compute-adjusted saturated categorical main-effects design; every "
            "requested level is retained and r-M_s, k-margin, C-communication "
            "sweeps vary one factor at a time."
        ),
    },
    "master_seeds": list(MASTER_SEEDS),
    "methods": list(METHODS),
    "runtime_symmetry": {
        "thread_count": 1,
        "environment_variables": {
            name: "1" for name in (
                "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
            )
        },
        "kernel_rule": (
            "Fresh uses baseline train_full independently; direct/basic/runner-up "
            "all use baseline unlearn with modes none/basic/runnerup"
        ),
    },
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


DECLARATION_SHA256 = hashlib.sha256(_canonical_json(DECLARATION).encode("utf-8")).hexdigest()
PREPROCESSING_ID = hashlib.sha256(
    _canonical_json(
        {
            key: DECLARATION[key]
            for key in (
                "acs_task", "acs_survey_year", "acs_horizon", "acs_survey",
                "geographic_filters", "feature_columns", "missing_value_rule",
                "categorical_encoding_rule", "standardization_rule",
                "two_group_definition", "natural_client_selection_rule",
                "natural_client_selection_seed", "record_subsampling_rule",
                "record_subsampling_seed",
            )
        }
    ).encode("utf-8")
).hexdigest()[:16]

DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "rtesults"
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "data" / "folktables"
RAW_NAME = "raw_results.csv"
AGGREGATED_NAME = "aggregated_results.csv"
DIAGNOSTICS_NAME = "client_diagnostics.csv"
DELETIONS_NAME = "deletion_batches.csv"
PREDECLARATION_NAME = "predeclaration.csv"
FIGURE_NAME = "acs_scaling_certificate.png"
TABLE_NAME = "compact_systems_table.csv"
REPORT_NAME = "report.md"


@dataclass(frozen=True)
class DesignPoint:
    design_index: int
    n: int
    C: int
    k: int
    T: int
    deletion_fraction: Decimal
    selection_reason: str

    @property
    def values(self) -> tuple[int, int, int, int, Decimal]:
        return self.n, self.C, self.k, self.T, self.deletion_fraction


def deletion_count(n: int, fraction: Decimal) -> int:
    rounded = int((Decimal(n) * fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(1, rounded)


def fractional_design() -> list[DesignPoint]:
    selected: OrderedDict[tuple[int, int, int, int, Decimal], list[str]] = OrderedDict()

    def add(values: tuple[int, int, int, int, Decimal], reason: str) -> None:
        selected.setdefault(values, []).append(reason)

    add(REFERENCE, "reference")
    for name, levels, position in (
        ("n", N_GRID, 0), ("C", C_GRID, 1), ("k", K_GRID, 2),
        ("T", T_GRID, 3), ("deletion fraction", DELETION_FRACTION_GRID, 4),
    ):
        for level in levels:
            values = list(REFERENCE)
            values[position] = level
            add(tuple(values), f"{name} sweep")
    return [
        DesignPoint(index, *values, selection_reason="; ".join(reasons))
        for index, (values, reasons) in enumerate(selected.items())
    ]


def design_matrix(points: Sequence[DesignPoint]) -> tuple[np.ndarray, list[str]]:
    levels = (N_GRID, C_GRID, K_GRID, T_GRID, DELETION_FRACTION_GRID)
    names = ("n", "C", "k", "T", "deletion_fraction")
    columns = ["intercept"]
    for name, factor_levels in zip(names, levels):
        columns.extend(f"{name}={level}" for level in factor_levels[1:])
    rows = []
    for point in points:
        row = [1.0]
        for value, factor_levels in zip(point.values, levels):
            row.extend(float(value == level) for level in factor_levels[1:])
        rows.append(row)
    return np.asarray(rows, dtype=np.float64), columns


def validate_fractional_design(points: Sequence[DesignPoint] | None = None) -> dict[str, Any]:
    chosen = list(points if points is not None else fractional_design())
    matrix, columns = design_matrix(chosen)
    rank = int(np.linalg.matrix_rank(matrix))
    if matrix.shape != (19, 19) or rank != 19:
        raise AssertionError(f"P3 main-effects matrix shape={matrix.shape}, rank={rank}; expected (19,19), rank 19")

    def relationship_rank(factor: str) -> int:
        index = {"n": 0, "C": 1, "k": 2, "T": 3, "r": 4}[factor]
        subset = [point for point in chosen if all(
            point.values[j] == REFERENCE[j] for j in range(5) if j != index
        )]
        values = [
            float(deletion_count(point.n, point.deletion_fraction)) if factor == "r"
            else float(point.values[index])
            for point in subset
        ]
        relation = np.column_stack((np.ones(len(values)), np.log(np.asarray(values))))
        return int(np.linalg.matrix_rank(relation))

    relationship_ranks = {
        "r_M_s": relationship_rank("r"),
        "k_margin": relationship_rank("k"),
        "C_communication": relationship_rank("C"),
    }
    if any(value != 2 for value in relationship_ranks.values()):
        raise AssertionError(f"rank-deficient required relationship sweep: {relationship_ranks}")
    return {"rank": rank, "columns": columns, "relationship_ranks": relationship_ranks}


DESIGN_VALIDATION = validate_fractional_design()
DECLARATION["fractional_design"]["analysis_matrix_rank"] = DESIGN_VALIDATION["rank"]
DECLARATION["fractional_design"]["analysis_matrix_columns"] = DESIGN_VALIDATION["columns"]
DECLARATION["fractional_design"]["relationship_matrix_ranks"] = DESIGN_VALIDATION[
    "relationship_ranks"
]
# Recompute after storing the validation itself.
DECLARATION_SHA256 = hashlib.sha256(_canonical_json(DECLARATION).encode("utf-8")).hexdigest()


@dataclass
class FrozenACSPool:
    state_data: dict[str, np.ndarray]
    state_groups: dict[str, np.ndarray]
    state_record_ids: dict[str, np.ndarray]
    puma_data: dict[str, np.ndarray]
    puma_groups: dict[str, np.ndarray]
    puma_record_ids: dict[str, np.ndarray]
    feature_mean: np.ndarray
    feature_std: np.ndarray
    fixed_point_clip: float
    source_files: tuple[str, ...]
    folktables_version: str

    def maps(self, C: int) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], str]:
        if C in (10, 25, 50):
            return self.state_data, self.state_groups, self.state_record_ids, "state"
        if C in (100, 250):
            return self.puma_data, self.puma_groups, self.puma_record_ids, "PUMA"
        raise ValueError(f"C={C} is outside the declared P3 grid")


@dataclass
class PreparedFederation:
    client_data: dict[int, np.ndarray]
    group_of: dict[int, np.ndarray]
    source_record_ids: dict[int, np.ndarray]
    geography_of: dict[int, str]
    eligible_sizes: dict[int, int]
    quotas: dict[int, int]
    client_type: str
    capacity: int
    sample_hash: str
    dataset_config_id: str
    permutation_hash: str
    selected_clients: tuple[str, ...]


def _derived_seed(base_seed: int, role: str, *values: object) -> int:
    digest = hashlib.sha256()
    digest.update(str(base_seed).encode("ascii"))
    digest.update(b"\0")
    digest.update(role.encode("utf-8"))
    for value in values:
        digest.update(b"\0")
        digest.update(str(value).encode("utf-8"))
    return int.from_bytes(digest.digest()[:8], "little", signed=False)


def _read_state_frame(data_dir: Path, state: str, download: bool):
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("P3 requires pandas") from exc

    year_dir = data_dir / str(DECLARATION["acs_survey_year"]) / DECLARATION["acs_horizon"]
    path = year_dir / f"psam_p{STATE_FIPS[state]:02d}.csv"
    columns = list(dict.fromkeys((*FEATURE_NAMES, "ST", "PUMA")))
    if path.exists():
        return pd.read_csv(path, usecols=columns, low_memory=False), path
    if not download:
        raise FileNotFoundError(f"missing frozen ACS file {path}; provide --data-dir or use --download")

    try:
        from folktables import ACSDataSource
    except ImportError as exc:
        raise RuntimeError("P3 requires folktables") from exc
    source = ACSDataSource(
        survey_year=str(DECLARATION["acs_survey_year"]),
        horizon=DECLARATION["acs_horizon"],
        survey=DECLARATION["acs_survey"],
        root_dir=str(data_dir),
    )
    frame = source.get_data(states=[state], density=1.0, random_seed=0, download=True)
    return frame.loc[:, columns], path


def load_acs_pool(data_dir: str | Path, download: bool = False) -> FrozenACSPool:
    """Load and globally standardize the fixed ACSEmployment population."""
    try:
        import folktables
        from folktables import ACSEmployment
    except ImportError as exc:
        raise RuntimeError("P3 requires folktables>=0.0.12") from exc

    if tuple(ACSEmployment.features) != FEATURE_NAMES:
        raise RuntimeError(
            "installed Folktables ACSEmployment schema differs from the frozen declaration: "
            f"{tuple(ACSEmployment.features)!r}"
        )

    root = Path(data_dir)
    raw_data: dict[str, np.ndarray] = {}
    raw_groups: dict[str, np.ndarray] = {}
    raw_pumas: dict[str, np.ndarray] = {}
    raw_record_ids: dict[str, np.ndarray] = {}
    source_files: list[str] = []

    for state in STATE_FIPS:
        frame, path = _read_state_frame(root, state, download)
        eligible = ACSEmployment._preprocess(frame)
        sex = eligible["SEX"].to_numpy(dtype=np.float64, copy=False)
        puma_float = eligible["PUMA"].to_numpy(dtype=np.float64, copy=False)
        valid = (
            np.isfinite(sex)
            & np.isin(sex, (1.0, 2.0))
            & np.isfinite(puma_float)
            & (puma_float > 0)
        )
        eligible = eligible.loc[valid]
        sex = sex[valid]
        puma_float = puma_float[valid]
        features = eligible.loc[:, list(FEATURE_NAMES)].to_numpy(dtype=np.float64, copy=True)
        features[np.isnan(features)] = -1.0
        if not np.isfinite(features).all():
            raise ValueError(f"non-finite feature remains after the declared rule in {state}")
        if features.shape[0] == 0:
            raise ValueError(f"eligible natural state client {state} is empty")

        raw_data[state] = features
        raw_groups[state] = np.where(sex == 1.0, 0, 1).astype(np.int64)
        raw_pumas[state] = puma_float.astype(np.int64)
        raw_record_ids[state] = eligible.index.to_numpy(dtype=np.int64, copy=True)
        source_files.append(str(path.resolve()))

    pooled = np.concatenate([raw_data[state] for state in STATE_FIPS], axis=0)
    feature_mean = pooled.mean(axis=0, dtype=np.float64)
    feature_std = pooled.std(axis=0, ddof=0, dtype=np.float64)
    feature_std = np.where(feature_std == 0.0, 1.0, feature_std)
    del pooled

    state_data: dict[str, np.ndarray] = {}
    state_groups: dict[str, np.ndarray] = {}
    state_ids: dict[str, np.ndarray] = {}
    puma_data: dict[str, np.ndarray] = {}
    puma_groups: dict[str, np.ndarray] = {}
    puma_ids: dict[str, np.ndarray] = {}
    max_abs = 0.0

    for state in STATE_FIPS:
        standardized = np.ascontiguousarray(
            (raw_data.pop(state) - feature_mean) / feature_std, dtype=np.float64
        )
        groups = np.ascontiguousarray(raw_groups.pop(state))
        pumas = raw_pumas.pop(state)
        record_ids = np.ascontiguousarray(raw_record_ids.pop(state))
        state_data[state] = standardized
        state_groups[state] = groups
        state_ids[state] = record_ids
        max_abs = max(max_abs, float(np.max(np.abs(standardized))))

        for puma in np.unique(pumas):
            mask = pumas == puma
            key = f"{state}:PUMA:{int(puma):05d}"
            puma_data[key] = np.ascontiguousarray(standardized[mask])
            puma_groups[key] = np.ascontiguousarray(groups[mask])
            puma_ids[key] = np.ascontiguousarray(record_ids[mask])

    return FrozenACSPool(
        state_data=state_data,
        state_groups=state_groups,
        state_record_ids=state_ids,
        puma_data=puma_data,
        puma_groups=puma_groups,
        puma_record_ids=puma_ids,
        feature_mean=feature_mean,
        feature_std=feature_std,
        fixed_point_clip=float(math.ceil(max_abs) + 1),
        source_files=tuple(source_files),
        folktables_version=getattr(folktables, "__version__", "unknown"),
    )


def natural_client_permutation(pool: FrozenACSPool, C: int) -> tuple[list[str], str, str]:
    data, _, _, client_type = pool.maps(C)
    keys = np.asarray(sorted(data), dtype=object)
    role = 0 if client_type == "state" else 1
    order = np.random.default_rng(
        np.random.SeedSequence([CLIENT_SELECTION_SEED, role])
    ).permutation(len(keys))
    permutation = [str(keys[index]) for index in order]
    digest = hashlib.sha256("\0".join(permutation).encode("utf-8")).hexdigest()
    return permutation, digest, client_type


def largest_remainder_quotas(sizes: Sequence[int], n: int) -> np.ndarray:
    sizes_array = np.asarray(sizes, dtype=np.int64)
    total = int(sizes_array.sum())
    if n > total:
        raise ValueError(f"requested n={n} exceeds selected-client capacity {total}")
    products = sizes_array * np.int64(n)
    quotas = products // total
    remainders = products % total
    remaining = int(n - int(quotas.sum()))
    # Stable sorting gives prefix position as the deterministic tie-break.
    order = np.argsort(-remainders, kind="stable")
    quotas[order[:remaining]] += 1
    if int(quotas.sum()) != n or np.any(quotas > sizes_array):
        raise AssertionError("largest-remainder allocation invariant failed")
    return quotas


def prepare_federation(
    pool: FrozenACSPool, n: int, C: int
) -> tuple[PreparedFederation | None, str | None]:
    source_data, source_groups, source_ids, client_type = pool.maps(C)
    permutation, permutation_hash, _ = natural_client_permutation(pool, C)
    if C > len(permutation):
        return None, f"only {len(permutation)} eligible natural {client_type} clients"
    selected = tuple(permutation[:C])
    sizes = np.asarray([source_data[key].shape[0] for key in selected], dtype=np.int64)
    capacity = int(sizes.sum())
    if n > capacity:
        return None, f"requested n={n} exceeds fixed-prefix capacity {capacity}"
    quotas = largest_remainder_quotas(sizes, n)
    if np.any(quotas == 0):
        return None, "largest-remainder allocation leaves a selected natural client empty"

    client_data: dict[int, np.ndarray] = {}
    group_of: dict[int, np.ndarray] = {}
    sampled_ids: dict[int, np.ndarray] = {}
    geography_of: dict[int, str] = {}
    eligible_sizes: dict[int, int] = {}
    quota_map: dict[int, int] = {}
    sample_digest = hashlib.sha256()

    for client_id, (geography, size, quota) in enumerate(zip(selected, sizes, quotas)):
        local_seed = _derived_seed(
            RECORD_SUBSAMPLING_SEED, "record-subsample", n, C, client_type, geography
        )
        if int(quota) == int(size):
            local_indices = np.arange(int(size), dtype=np.int64)
        else:
            local_indices = np.sort(
                np.random.default_rng(local_seed).choice(
                    int(size), size=int(quota), replace=False
                ).astype(np.int64)
            )
        client_data[client_id] = np.ascontiguousarray(source_data[geography][local_indices])
        group_of[client_id] = np.ascontiguousarray(source_groups[geography][local_indices])
        sampled_ids[client_id] = np.ascontiguousarray(source_ids[geography][local_indices])
        geography_of[client_id] = geography
        eligible_sizes[client_id] = int(size)
        quota_map[client_id] = int(quota)
        sample_digest.update(geography.encode("utf-8"))
        sample_digest.update(np.asarray(sampled_ids[client_id], dtype="<i8").tobytes())

    n_a = int(sum(np.sum(groups == 0) for groups in group_of.values()))
    n_b = int(sum(np.sum(groups == 1) for groups in group_of.values()))
    if n_a == 0 or n_b == 0:
        return None, "declared global group is empty after deterministic sampling"
    if any(values.shape[0] == 0 for values in client_data.values()):
        return None, "selected natural client is empty after deterministic sampling"

    dataset_key = {
        "preprocessing_id": PREPROCESSING_ID,
        "task": DECLARATION["acs_task"],
        "year": DECLARATION["acs_survey_year"],
        "n": n,
        "C": C,
        "client_type": client_type,
        "sample_hash": sample_digest.hexdigest(),
    }
    dataset_config_id = hashlib.sha256(
        _canonical_json(dataset_key).encode("utf-8")
    ).hexdigest()[:20]
    return PreparedFederation(
        client_data=client_data,
        group_of=group_of,
        source_record_ids=sampled_ids,
        geography_of=geography_of,
        eligible_sizes=eligible_sizes,
        quotas=quota_map,
        client_type=client_type,
        capacity=capacity,
        sample_hash=sample_digest.hexdigest(),
        dataset_config_id=dataset_config_id,
        permutation_hash=permutation_hash,
        selected_clients=selected,
    ), None


def federation_diagnostic_rows(federation: PreparedFederation, n: int, C: int) -> list[dict[str, Any]]:
    n_a = int(sum(np.sum(groups == 0) for groups in federation.group_of.values()))
    n_b = int(sum(np.sum(groups == 1) for groups in federation.group_of.values()))
    preliminary = []
    factors = []
    for client_id in sorted(federation.client_data):
        groups = federation.group_of[client_id]
        n_c = int(groups.size)
        n_c_a = int(np.sum(groups == 0))
        n_c_b = int(np.sum(groups == 1))
        prop_a, prop_b = n_c_a / n_c, n_c_b / n_c
        a_c, b_c = n_c_a / n_a, n_c_b / n_b
        pure = n_c_a == 0 or n_c_b == 0
        component = 1.0 if pure else max(a_c / b_c, b_c / a_c)
        nearly = (not pure) and max(prop_a, prop_b) >= NEARLY_PURE_THRESHOLD
        factors.append(component)
        preliminary.append(
            (client_id, n_c, n_c_a, n_c_b, prop_a, prop_b, a_c, b_c,
             pure, nearly, component)
        )
    empirical_kappa = max(1.0, max(factors, default=1.0))
    pure_count = sum(int(row[8]) for row in preliminary)
    nearly_count = sum(int(row[9]) for row in preliminary)
    rows = []
    for (client_id, n_c, n_c_a, n_c_b, prop_a, prop_b, a_c, b_c,
         pure, nearly, component) in preliminary:
        values = federation.client_data[client_id]
        means = values.mean(axis=0, dtype=np.float64)
        stds = values.std(axis=0, ddof=0, dtype=np.float64)
        row: dict[str, Any] = {
            "schema_version": 1,
            "declaration_sha256": DECLARATION_SHA256,
            "preprocessing_id": PREPROCESSING_ID,
            "acs_task": DECLARATION["acs_task"],
            "acs_survey_year": DECLARATION["acs_survey_year"],
            "dataset_config_id": federation.dataset_config_id,
            "n": n,
            "C": C,
            "d": len(FEATURE_NAMES),
            "natural_client_type": federation.client_type,
            "client_id": client_id,
            "geography": federation.geography_of[client_id],
            "client_prefix_position": client_id,
            "eligible_client_records": federation.eligible_sizes[client_id],
            "client_size": n_c,
            "group_A_count": n_c_a,
            "group_B_count": n_c_b,
            "group_A_proportion": prop_a,
            "group_B_proportion": prop_b,
            "global_group_A_count": n_a,
            "global_group_B_count": n_b,
            "a_c": a_c,
            "b_c": b_c,
            "kappa_component": component,
            "empirical_kappa": empirical_kappa,
            "pure_client": pure,
            "pure_group": "A" if pure and n_c_a else ("B" if pure else ""),
            "nearly_pure_client": nearly,
            "nearly_pure_threshold": NEARLY_PURE_THRESHOLD,
            "group_A_slice_empty": n_c_a == 0,
            "group_A_slice_nonempty": n_c_a > 0,
            "group_B_slice_empty": n_c_b == 0,
            "group_B_slice_nonempty": n_c_b > 0,
            "pure_client_count": pure_count,
            "nearly_pure_client_count": nearly_count,
            "selected_client_capacity": federation.capacity,
            "sample_hash": federation.sample_hash,
            "client_selection_permutation_sha256": federation.permutation_hash,
            "selected_clients_json": _canonical_json(federation.selected_clients),
        }
        for feature, mean, std in zip(FEATURE_NAMES, means, stds):
            row[f"feature_mean_{feature}"] = float(mean)
            row[f"feature_std_{feature}"] = float(std)
        rows.append(row)
    return rows


def sample_deletion(
    federation: PreparedFederation,
    point: DesignPoint,
    master_seed: int,
) -> tuple[dict[int, np.ndarray], str, int, list[dict[str, Any]]]:
    r = deletion_count(point.n, point.deletion_fraction)
    if r >= point.n:
        raise ValueError(f"invalid deletion size r={r} for n={point.n}")
    client_ids = sorted(federation.client_data)
    sizes = np.asarray([federation.client_data[c].shape[0] for c in client_ids], dtype=np.int64)
    offsets = np.concatenate((np.asarray([0], dtype=np.int64), np.cumsum(sizes)))
    deletion_seed = _derived_seed(
        DELETION_SAMPLING_SEED,
        "uniform-deletion",
        master_seed,
        point.n,
        point.C,
        point.k,
        point.T,
        format(point.deletion_fraction, "f"),
    )
    selected: np.ndarray | None = None
    removed: dict[int, np.ndarray] = {}
    for attempt in range(100):
        rng = np.random.default_rng(
            _derived_seed(deletion_seed, "validity-attempt", attempt)
        )
        candidate = np.sort(rng.choice(point.n, size=r, replace=False).astype(np.int64))
        positions = np.searchsorted(offsets, candidate, side="right") - 1
        proposed = {}
        for position, client_id in enumerate(client_ids):
            local = candidate[positions == position] - offsets[position]
            if local.size:
                proposed[client_id] = np.ascontiguousarray(local, dtype=np.int64)
        retained_groups = [0, 0]
        for client_id, groups in federation.group_of.items():
            mask = np.ones(groups.size, dtype=bool)
            mask[proposed.get(client_id, np.empty(0, dtype=np.int64))] = False
            retained_groups[0] += int(np.sum((groups == 0) & mask))
            retained_groups[1] += int(np.sum((groups == 1) & mask))
        if retained_groups[0] > 0 and retained_groups[1] > 0:
            selected, removed = candidate, proposed
            break
    if selected is None:
        raise RuntimeError("could not draw a valid uniform deletion in 100 attempts")

    archive_rows = []
    digest = hashlib.sha256()
    positions = np.searchsorted(offsets, selected, side="right") - 1
    for flat_index, position in zip(selected, positions):
        client_id = client_ids[int(position)]
        local_index = int(flat_index - offsets[int(position)])
        geography = federation.geography_of[client_id]
        source_row_id = int(federation.source_record_ids[client_id][local_index])
        stable_id = f"{geography}:source-row:{source_row_id}"
        digest.update(stable_id.encode("utf-8"))
        digest.update(b"\0")
        archive_rows.append(
            {
                "declaration_sha256": DECLARATION_SHA256,
                "dataset_config_id": federation.dataset_config_id,
                "design_index": point.design_index,
                "master_seed": master_seed,
                "deletion_seed": deletion_seed,
                "requested_deletion_fraction": format(point.deletion_fraction, "f"),
                "r": r,
                "flat_sample_index": int(flat_index),
                "client_id": client_id,
                "geography": geography,
                "local_sample_index": local_index,
                "source_row_id": source_row_id,
                "stable_record_id": stable_id,
            }
        )
    deletion_hash = digest.hexdigest()
    for row in archive_rows:
        row["deletion_batch_hash"] = deletion_hash
    return removed, deletion_hash, deletion_seed, archive_rows


def apply_deletion(
    federation: PreparedFederation, removed: Mapping[int, np.ndarray]
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    retained_data, retained_groups = {}, {}
    for client_id in sorted(federation.client_data):
        mask = np.ones(federation.client_data[client_id].shape[0], dtype=bool)
        mask[removed.get(client_id, np.empty(0, dtype=np.int64))] = False
        retained_data[client_id] = np.ascontiguousarray(federation.client_data[client_id][mask])
        retained_groups[client_id] = np.ascontiguousarray(federation.group_of[client_id][mask])
    return retained_data, retained_groups


def touched_slice_statistics(
    federation: PreparedFederation, removed: Mapping[int, np.ndarray]
) -> tuple[int, list[dict[str, Any]]]:
    touched = []
    mass = 0
    for client_id in sorted(removed):
        deleted_groups = federation.group_of[client_id][removed[client_id]]
        for group_id in sorted(np.unique(deleted_groups).tolist()):
            original = int(np.sum(federation.group_of[client_id] == group_id))
            deleted = int(np.sum(deleted_groups == group_id))
            retained = original - deleted
            mass += retained
            touched.append(
                {
                    "client_id": client_id,
                    "geography": federation.geography_of[client_id],
                    "group": "A" if group_id == 0 else "B",
                    "original_slice_size": original,
                    "deleted_from_slice": deleted,
                    "retained_slice_size": retained,
                }
            )
    return mass, touched


def retained_margin_statistics(
    checkpoint: dict, removed: Mapping[int, np.ndarray]
) -> dict[str, Any]:
    retained_masks = {}
    for client_id in checkpoint["client_ids"]:
        mask = np.ones(checkpoint["client_data"][client_id].shape[0], dtype=bool)
        mask[removed.get(client_id, np.empty(0, dtype=np.int64))] = False
        retained_masks[client_id] = mask

    round_rows = []
    all_rounds = []
    for round_index in range(checkpoint["T"]):
        parts = []
        for client_id in checkpoint["client_ids"]:
            cached = checkpoint["client_cache"][client_id][round_index]
            parts.append((cached["d2"] - cached["d1"])[retained_masks[client_id]])
        margins = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
        all_rounds.append(margins)
        round_rows.append(
            {
                "round": round_index,
                "count": int(margins.size),
                "mean": float(np.mean(margins)),
                "std": float(np.std(margins, ddof=0)),
                "median": float(np.median(margins)),
                "min": float(np.min(margins)),
                "max": float(np.max(margins)),
            }
        )
    all_margins = np.concatenate(all_rounds)
    return {
        "count": int(all_margins.size),
        "mean": float(np.mean(all_margins)),
        "std": float(np.std(all_margins, ddof=0)),
        "median": float(np.median(all_margins)),
        "min": float(np.min(all_margins)),
        "max": float(np.max(all_margins)),
        "rounds": round_rows,
    }


def certificate_statistics(replay: dict, checkpoint: dict) -> dict[str, Any]:
    tested = 0
    accepted = 0
    round_rows = []
    all_deltas = []
    for round_index, diagnostic in enumerate(replay["diagnostics"]):
        round_tested = int(diagnostic["certified"] + diagnostic["failing"])
        round_accepted = int(diagnostic["certified"])
        delta = np.sqrt(
            np.sum(
                (replay["trajectory"][round_index] - checkpoint["trajectory"][round_index]) ** 2,
                axis=1,
            )
        )
        all_deltas.append(delta)
        tested += round_tested
        accepted += round_accepted
        round_rows.append(
            {
                "round": round_index,
                "tested": round_tested,
                "accepted": round_accepted,
                "pass_rate": round_accepted / round_tested if round_tested else None,
                "delta_mean": float(np.mean(delta)),
                "delta_max": float(np.max(delta)),
                "abandoned_this_round": bool(diagnostic["abandoned_this_round"]),
            }
        )
    flat_delta = np.concatenate(all_deltas)
    return {
        "tested": tested,
        "accepted": accepted,
        "pass_rate": accepted / tested if tested else None,
        "abandonment_round": replay["abandonment_round"],
        "center_shift_mean": float(np.mean(flat_delta)),
        "center_shift_max": float(np.max(flat_delta)),
        "rounds": round_rows,
    }


@dataclass
class CommunicationCounter:
    k: int
    d: int
    phase_i_slice_messages: int = 0
    phase_i_anchor_scalars: int = 0
    phase_ii_stat_messages: int = 0

    @property
    def phase_ii_stat_scalars(self) -> int:
        return self.phase_ii_stat_messages * 2 * self.k * (self.d + 2)

    @property
    def total_numeric_scalars(self) -> int:
        return self.phase_i_anchor_scalars + self.phase_ii_stat_scalars

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase_i_slice_messages": self.phase_i_slice_messages,
            "phase_i_anchor_scalars": self.phase_i_anchor_scalars,
            "phase_ii_stat_messages": self.phase_ii_stat_messages,
            "phase_ii_stat_scalars": self.phase_ii_stat_scalars,
            "total_numeric_scalars": self.total_numeric_scalars,
        }


@contextmanager
def count_existing_communication(module: Any, k: int, d: int):
    """Observe existing summary calls without changing their returned values."""
    counter = CommunicationCounter(k=k, d=d)
    original_local = module.local_slice_step
    original_accumulate = module.accumulate_stats

    def counted_local(*args, **kwargs):
        result = original_local(*args, **kwargs)
        counter.phase_i_slice_messages += 1
        counter.phase_i_anchor_scalars += int(result["k_e"]) * (d + 1)
        return result

    def counted_accumulate(*args, **kwargs):
        result = original_accumulate(*args, **kwargs)
        counter.phase_ii_stat_messages += 1
        return result

    module.local_slice_step = counted_local
    module.accumulate_stats = counted_accumulate
    try:
        yield counter
    finally:
        module.local_slice_step = original_local
        module.accumulate_stats = original_accumulate


def timed_train(
    client_data: dict[int, np.ndarray],
    group_of: dict[int, np.ndarray],
    seed: int,
    k: int,
    T: int,
    fp_cfg: FixedPointConfig,
) -> tuple[dict, float, dict[str, Any]]:
    gc.collect()
    with count_existing_communication(baseline_train, k, len(FEATURE_NAMES)) as counter:
        start = time.perf_counter()
        result = baseline_train.train_full(
            client_data,
            group_of,
            seed,
            k,
            T,
            L_BISECTION,
            gamma=GAMMA,
            fp_cfg=fp_cfg,
            anchor_lloyd_iters=ANCHOR_LLOYD_ITERS,
        )
        elapsed = time.perf_counter() - start
    return result, elapsed, counter.as_dict()


def timed_replay(
    checkpoint: dict,
    removed: Mapping[int, np.ndarray],
    mode: str,
) -> tuple[dict, float, dict[str, Any]]:
    gc.collect()
    with count_existing_communication(
        baseline_unlearn, checkpoint["k"], len(FEATURE_NAMES)
    ) as counter:
        start = time.perf_counter()
        result = baseline_unlearn.unlearn(
            checkpoint,
            removed,
            certificate_mode=mode,
            abandon_threshold=ABANDON_THRESHOLD,
        )
        elapsed = time.perf_counter() - start
    return result, elapsed, counter.as_dict()


RAW_FIELDS = (
    "schema_version", "experiment", "declaration_sha256", "preprocessing_id",
    "status", "error", "design_type", "design_index", "selection_reason",
    "design_matrix_rank", "relationship_matrix_ranks_json",
    "acs_task", "acs_survey_year", "acs_horizon", "acs_survey",
    "geographic_filters_json", "feature_columns_json", "missing_value_rule",
    "categorical_encoding_rule", "standardization_rule", "two_group_definition",
    "client_selection_rule", "client_selection_seed", "record_subsampling_rule",
    "record_subsampling_seed", "deletion_sampling_rule", "deletion_sampling_seed_base",
    "nearly_pure_threshold", "master_seed", "master_seed_list_json",
    "dataset_config_id", "data_sample_hash", "client_selection_permutation_sha256",
    "selected_clients_json", "natural_client_type", "selected_client_capacity",
    "n", "C", "k", "T", "d", "L_bisection", "gamma", "scale_bits",
    "fixed_point_clip", "anchor_lloyd_iters", "certificate_abandon_threshold",
    "requested_deletion_fraction", "deletion_size_r", "realized_deletion_fraction",
    "deletion_seed", "deletion_batch_hash", "deletion_archive_csv",
    "empirical_kappa", "pure_client_count", "nearly_pure_client_count",
    "M_s", "touched_slices_json", "method", "total_runtime_seconds",
    "setup_train_seconds", "setup_communication_numeric_scalars",
    "communication_unit", "communication_rule", "communication_phase_i_slice_messages",
    "communication_phase_i_anchor_scalars", "communication_phase_ii_stat_messages",
    "communication_phase_ii_stat_scalars", "communication_numeric_scalars",
    "margin_count", "margin_mean", "margin_std", "margin_median", "margin_min",
    "margin_max", "margin_rounds_json", "center_shift_mean", "center_shift_max",
    "certificate_tested_labels", "certificate_accepted_labels", "certificate_pass_rate",
    "certificate_abandonment_round", "certificate_rounds_json",
    "exact_replay_matches_fresh", "thread_count", "runtime_environment_json",
)

DIAGNOSTIC_FIELDS = (
    "schema_version", "declaration_sha256", "preprocessing_id", "acs_task",
    "acs_survey_year", "dataset_config_id", "n", "C", "d", "natural_client_type",
    "client_id", "geography", "client_prefix_position", "eligible_client_records",
    "client_size", "group_A_count", "group_B_count", "group_A_proportion",
    "group_B_proportion", "global_group_A_count", "global_group_B_count", "a_c",
    "b_c", "kappa_component", "empirical_kappa", "pure_client", "pure_group",
    "nearly_pure_client", "nearly_pure_threshold", "group_A_slice_empty",
    "group_A_slice_nonempty", "group_B_slice_empty", "group_B_slice_nonempty",
    "pure_client_count", "nearly_pure_client_count", "selected_client_capacity",
    "sample_hash", "client_selection_permutation_sha256", "selected_clients_json",
) + tuple(
    field
    for feature in FEATURE_NAMES
    for field in (f"feature_mean_{feature}", f"feature_std_{feature}")
)

DELETION_FIELDS = (
    "declaration_sha256", "dataset_config_id", "design_index", "master_seed",
    "deletion_seed", "requested_deletion_fraction", "r", "deletion_batch_hash",
    "flat_sample_index", "client_id", "geography", "local_sample_index",
    "source_row_id", "stable_record_id",
)


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _append_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
        output.flush()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def write_predeclaration(output_dir: Path) -> Path:
    row = {
        "declaration_sha256": DECLARATION_SHA256,
        "experiment": DECLARATION["experiment"],
        "acs_task": DECLARATION["acs_task"],
        "acs_survey_year": DECLARATION["acs_survey_year"],
        "acs_horizon": DECLARATION["acs_horizon"],
        "acs_survey": DECLARATION["acs_survey"],
        "geographic_filters_json": _canonical_json(DECLARATION["geographic_filters"]),
        "feature_columns_json": _canonical_json(FEATURE_NAMES),
        "missing_value_rule": MISSING_VALUE_RULE,
        "categorical_encoding_rule": CATEGORICAL_ENCODING_RULE,
        "standardization_rule": STANDARDIZATION_RULE,
        "two_group_definition": GROUP_RULE,
        "natural_client_selection_rule": CLIENT_SELECTION_RULE,
        "natural_client_selection_seed": CLIENT_SELECTION_SEED,
        "record_subsampling_rule": RECORD_SUBSAMPLING_RULE,
        "record_subsampling_seed": RECORD_SUBSAMPLING_SEED,
        "deletion_sampling_rule": DELETION_SAMPLING_RULE,
        "deletion_sampling_seed": DELETION_SAMPLING_SEED,
        "nearly_pure_threshold": NEARLY_PURE_THRESHOLD,
        "n_grid_json": _canonical_json(N_GRID),
        "C_grid_json": _canonical_json(C_GRID),
        "k_grid_json": _canonical_json(K_GRID),
        "T_grid_json": _canonical_json(T_GRID),
        "deletion_fraction_grid_json": _canonical_json(
            [format(value, "f") for value in DELETION_FRACTION_GRID]
        ),
        "master_seeds_json": _canonical_json(MASTER_SEEDS),
        "methods_json": _canonical_json(tuple(METHODS)),
        "fractional_reference_json": _canonical_json(
            [REFERENCE[0], REFERENCE[1], REFERENCE[2], REFERENCE[3], format(REFERENCE[4], "f")]
        ),
        "design_matrix_rank": DESIGN_VALIDATION["rank"],
        "design_matrix_columns_json": _canonical_json(DESIGN_VALIDATION["columns"]),
        "relationship_matrix_ranks_json": _canonical_json(DESIGN_VALIDATION["relationship_ranks"]),
        "communication_rule": COMMUNICATION_RULE,
        "thread_count": 1,
    }
    path = output_dir / PREDECLARATION_NAME
    if path.exists():
        existing = _read_csv(path)
        if len(existing) != 1 or existing[0].get("declaration_sha256") != DECLARATION_SHA256:
            raise ValueError(f"existing {path} has a different P3 declaration")
        return path
    _write_csv(path, tuple(row), [row])
    return path


def _dataset_summary(diagnostic_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    first = diagnostic_rows[0]
    return {
        "empirical_kappa": first["empirical_kappa"],
        "pure_client_count": first["pure_client_count"],
        "nearly_pure_client_count": first["nearly_pure_client_count"],
    }


def _base_raw_row(
    point: DesignPoint,
    master_seed: int,
    federation: PreparedFederation,
    pool: FrozenACSPool,
    dataset_summary: Mapping[str, Any],
    deletion_hash: str,
    deletion_seed: int,
    M_s: int,
    touched_slices: Sequence[Mapping[str, Any]],
    setup_seconds: float,
    setup_comm: Mapping[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    r = deletion_count(point.n, point.deletion_fraction)
    return {
        "schema_version": 1,
        "experiment": DECLARATION["experiment"],
        "declaration_sha256": DECLARATION_SHA256,
        "preprocessing_id": PREPROCESSING_ID,
        "status": "complete",
        "error": "",
        "design_type": "fractional-reference-sweeps",
        "design_index": point.design_index,
        "selection_reason": point.selection_reason,
        "design_matrix_rank": DESIGN_VALIDATION["rank"],
        "relationship_matrix_ranks_json": _canonical_json(DESIGN_VALIDATION["relationship_ranks"]),
        "acs_task": DECLARATION["acs_task"],
        "acs_survey_year": DECLARATION["acs_survey_year"],
        "acs_horizon": DECLARATION["acs_horizon"],
        "acs_survey": DECLARATION["acs_survey"],
        "geographic_filters_json": _canonical_json(DECLARATION["geographic_filters"]),
        "feature_columns_json": _canonical_json(FEATURE_NAMES),
        "missing_value_rule": MISSING_VALUE_RULE,
        "categorical_encoding_rule": CATEGORICAL_ENCODING_RULE,
        "standardization_rule": STANDARDIZATION_RULE,
        "two_group_definition": GROUP_RULE,
        "client_selection_rule": CLIENT_SELECTION_RULE,
        "client_selection_seed": CLIENT_SELECTION_SEED,
        "record_subsampling_rule": RECORD_SUBSAMPLING_RULE,
        "record_subsampling_seed": RECORD_SUBSAMPLING_SEED,
        "deletion_sampling_rule": DELETION_SAMPLING_RULE,
        "deletion_sampling_seed_base": DELETION_SAMPLING_SEED,
        "nearly_pure_threshold": NEARLY_PURE_THRESHOLD,
        "master_seed": master_seed,
        "master_seed_list_json": _canonical_json(MASTER_SEEDS),
        "dataset_config_id": federation.dataset_config_id,
        "data_sample_hash": federation.sample_hash,
        "client_selection_permutation_sha256": federation.permutation_hash,
        "selected_clients_json": _canonical_json(federation.selected_clients),
        "natural_client_type": federation.client_type,
        "selected_client_capacity": federation.capacity,
        "n": point.n,
        "C": point.C,
        "k": point.k,
        "T": point.T,
        "d": len(FEATURE_NAMES),
        "L_bisection": L_BISECTION,
        "gamma": GAMMA,
        "scale_bits": SCALE_BITS,
        "fixed_point_clip": pool.fixed_point_clip,
        "anchor_lloyd_iters": ANCHOR_LLOYD_ITERS,
        "certificate_abandon_threshold": ABANDON_THRESHOLD,
        "requested_deletion_fraction": format(point.deletion_fraction, "f"),
        "deletion_size_r": r,
        "realized_deletion_fraction": r / point.n,
        "deletion_seed": deletion_seed,
        "deletion_batch_hash": deletion_hash,
        "deletion_archive_csv": str((output_dir / DELETIONS_NAME).resolve()),
        "empirical_kappa": dataset_summary["empirical_kappa"],
        "pure_client_count": dataset_summary["pure_client_count"],
        "nearly_pure_client_count": dataset_summary["nearly_pure_client_count"],
        "M_s": M_s,
        "touched_slices_json": _canonical_json(touched_slices),
        "method": "",
        "total_runtime_seconds": "",
        "setup_train_seconds": setup_seconds,
        "setup_communication_numeric_scalars": setup_comm["total_numeric_scalars"],
        "communication_unit": "numeric scalars",
        "communication_rule": COMMUNICATION_RULE,
        "communication_phase_i_slice_messages": "",
        "communication_phase_i_anchor_scalars": "",
        "communication_phase_ii_stat_messages": "",
        "communication_phase_ii_stat_scalars": "",
        "communication_numeric_scalars": "",
        "margin_count": "",
        "margin_mean": "",
        "margin_std": "",
        "margin_median": "",
        "margin_min": "",
        "margin_max": "",
        "margin_rounds_json": "",
        "center_shift_mean": "",
        "center_shift_max": "",
        "certificate_tested_labels": "",
        "certificate_accepted_labels": "",
        "certificate_pass_rate": "",
        "certificate_abandonment_round": "",
        "certificate_rounds_json": "",
        "exact_replay_matches_fresh": "",
        "thread_count": 1,
        "runtime_environment_json": _canonical_json(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "numpy": np.__version__,
                "threads": 1,
            }
        ),
    }


def _set_communication(row: dict[str, Any], communication: Mapping[str, Any]) -> None:
    row["communication_phase_i_slice_messages"] = communication["phase_i_slice_messages"]
    row["communication_phase_i_anchor_scalars"] = communication["phase_i_anchor_scalars"]
    row["communication_phase_ii_stat_messages"] = communication["phase_ii_stat_messages"]
    row["communication_phase_ii_stat_scalars"] = communication["phase_ii_stat_scalars"]
    row["communication_numeric_scalars"] = communication["total_numeric_scalars"]


def _set_margin(row: dict[str, Any], margin: Mapping[str, Any]) -> None:
    for name in ("count", "mean", "std", "median", "min", "max"):
        row[f"margin_{name}"] = margin[name]
    row["margin_rounds_json"] = _canonical_json(margin["rounds"])


def execute_deletion_request(
    point: DesignPoint,
    master_seed: int,
    federation: PreparedFederation,
    pool: FrozenACSPool,
    dataset_summary: Mapping[str, Any],
    checkpoint: dict,
    setup_seconds: float,
    setup_comm: Mapping[str, Any],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    removed, deletion_hash, deletion_seed, archive_rows = sample_deletion(
        federation, point, master_seed
    )
    M_s, touched_slices = touched_slice_statistics(federation, removed)
    margin = retained_margin_statistics(checkpoint, removed)
    retained_data, retained_groups = apply_deletion(federation, removed)
    common = _base_raw_row(
        point, master_seed, federation, pool, dataset_summary,
        deletion_hash, deletion_seed, M_s, touched_slices,
        setup_seconds, setup_comm, output_dir,
    )

    fp_cfg = checkpoint["fp_cfg"]
    fresh, elapsed, communication = timed_train(
        retained_data, retained_groups, master_seed, point.k, point.T, fp_cfg
    )
    fresh_digests = list(fresh["digests"])
    fresh_centers = fresh["final_centers"].copy()
    fresh_row = dict(common)
    fresh_row["method"] = "Fresh Retraining"
    fresh_row["total_runtime_seconds"] = elapsed
    _set_communication(fresh_row, communication)
    rows = [fresh_row]
    del fresh
    gc.collect()

    for method, mode in list(METHODS.items())[1:]:
        replay, elapsed, communication = timed_replay(checkpoint, removed, mode)
        exact = replay["digests"] == fresh_digests and np.array_equal(
            replay["final_centers"], fresh_centers
        )
        row = dict(common)
        row["method"] = method
        row["total_runtime_seconds"] = elapsed
        row["exact_replay_matches_fresh"] = exact
        row["status"] = "complete" if exact else "exactness_failure"
        if not exact:
            row["error"] = "replay digests and/or indexed final centers differ from fresh retraining"
        _set_communication(row, communication)
        if mode in ("basic", "runnerup"):
            _set_margin(row, margin)
            certificate = certificate_statistics(replay, checkpoint)
            row["center_shift_mean"] = certificate["center_shift_mean"]
            row["center_shift_max"] = certificate["center_shift_max"]
            row["certificate_tested_labels"] = certificate["tested"]
            row["certificate_accepted_labels"] = certificate["accepted"]
            row["certificate_pass_rate"] = (
                "" if certificate["pass_rate"] is None else certificate["pass_rate"]
            )
            row["certificate_abandonment_round"] = (
                "" if certificate["abandonment_round"] is None
                else certificate["abandonment_round"]
            )
            row["certificate_rounds_json"] = _canonical_json(certificate["rounds"])
        rows.append(row)
        del replay
        gc.collect()
    return rows, archive_rows


def _completed_raw_keys(path: Path) -> set[tuple[int, int, str]]:
    if not path.exists():
        return set()
    keys = set()
    for row in _read_csv(path):
        if row.get("declaration_sha256") != DECLARATION_SHA256:
            raise ValueError(f"{path} contains a different P3 declaration")
        keys.add((int(row["design_index"]), int(row["master_seed"]), row["method"]))
    return keys


def run_experiment(data_dir: Path, output_dir: Path, download: bool, resume: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_predeclaration(output_dir)
    raw_path = output_dir / RAW_NAME
    if raw_path.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite {raw_path}; use --resume")
    completed = _completed_raw_keys(raw_path) if resume else set()
    points = fractional_design()

    print(
        f"[P3 declaration] task={DECLARATION['acs_task']} year={DECLARATION['acs_survey_year']} "
        f"seeds={list(MASTER_SEEDS)} points={len(points)} rank={DESIGN_VALIDATION['rank']}",
        flush=True,
    )
    print(f"[P3 declaration sha256] {DECLARATION_SHA256}", flush=True)
    load_start = time.perf_counter()
    pool = load_acs_pool(data_dir, download=download)
    print(
        f"[ACS loaded] records={sum(len(v) for v in pool.state_data.values())} "
        f"states={len(pool.state_data)} PUMAs={len(pool.puma_data)} d={len(FEATURE_NAMES)} "
        f"clip={pool.fixed_point_clip:g} seconds={time.perf_counter()-load_start:.2f}",
        flush=True,
    )

    dataset_pairs = list(OrderedDict.fromkeys((point.n, point.C) for point in points))
    federations: dict[tuple[int, int], PreparedFederation] = {}
    diagnostic_by_pair: dict[tuple[int, int], list[dict[str, Any]]] = {}
    unavailable: dict[tuple[int, int], str] = {}
    for n, C in dataset_pairs:
        federation, reason = prepare_federation(pool, n, C)
        if federation is None:
            unavailable[(n, C)] = str(reason)
            print(f"[dataset unavailable] n={n} C={C}: {reason}", flush=True)
        else:
            federations[(n, C)] = federation
            diagnostic_by_pair[(n, C)] = federation_diagnostic_rows(federation, n, C)
            print(
                f"[dataset ready] n={n} C={C} type={federation.client_type} "
                f"capacity={federation.capacity} id={federation.dataset_config_id}",
                flush=True,
            )

    available_points = [point for point in points if (point.n, point.C) in federations]
    available_matrix, _ = design_matrix(available_points)
    available_rank = int(np.linalg.matrix_rank(available_matrix))
    if unavailable or available_rank != DESIGN_VALIDATION["rank"]:
        raise RuntimeError(
            "the fixed natural-client prefixes make the declared fractional design unavailable: "
            f"unavailable={unavailable}, available main-effects rank={available_rank}"
        )

    diagnostics_path = output_dir / DIAGNOSTICS_NAME
    if not diagnostics_path.exists():
        _write_csv(
            diagnostics_path,
            DIAGNOSTIC_FIELDS,
            [row for pair in dataset_pairs for row in diagnostic_by_pair[pair]],
        )
    else:
        existing = _read_csv(diagnostics_path)
        if any(row.get("declaration_sha256") != DECLARATION_SHA256 for row in existing):
            raise ValueError(f"{diagnostics_path} contains a different P3 declaration")
        present = {row["dataset_config_id"] for row in existing}
        additions = [
            row for pair in dataset_pairs for row in diagnostic_by_pair[pair]
            if row["dataset_config_id"] not in present
        ]
        if additions:
            _append_csv(diagnostics_path, DIAGNOSTIC_FIELDS, additions)

    deletion_path = output_dir / DELETIONS_NAME
    archived_batches = set()
    if deletion_path.exists():
        archived_batches = {row["deletion_batch_hash"] for row in _read_csv(deletion_path)}

    fp_cfg = FixedPointConfig(scale_bits=SCALE_BITS, clip=pool.fixed_point_clip)
    total_requests = len(points) * len(MASTER_SEEDS)
    request_number = 0
    failure_count = 0
    for master_seed in MASTER_SEEDS:
        groups: OrderedDict[tuple[int, int, int, int], list[DesignPoint]] = OrderedDict()
        for point in points:
            if all((point.design_index, master_seed, method) in completed for method in METHODS):
                request_number += 1
                continue
            groups.setdefault((point.n, point.C, point.k, point.T), []).append(point)

        for (n, C, k, T), deletion_points in groups.items():
            federation = federations[(n, C)]
            checkpoint, setup_seconds, setup_comm = timed_train(
                federation.client_data, federation.group_of, master_seed, k, T, fp_cfg
            )
            dataset_summary = _dataset_summary(diagnostic_by_pair[(n, C)])
            for point in deletion_points:
                request_number += 1
                start = time.perf_counter()
                rows, archive_rows = execute_deletion_request(
                    point,
                    master_seed,
                    federation,
                    pool,
                    dataset_summary,
                    checkpoint,
                    setup_seconds,
                    setup_comm,
                    output_dir,
                )
                if archive_rows and archive_rows[0]["deletion_batch_hash"] not in archived_batches:
                    _append_csv(deletion_path, DELETION_FIELDS, archive_rows)
                    archived_batches.add(archive_rows[0]["deletion_batch_hash"])
                new_rows = [
                    row for row in rows
                    if (point.design_index, master_seed, row["method"]) not in completed
                ]
                _append_csv(raw_path, RAW_FIELDS, new_rows)
                for row in new_rows:
                    completed.add((point.design_index, master_seed, row["method"]))
                failures = sum(row["status"] != "complete" for row in rows)
                failure_count += failures
                print(
                    f"[request {request_number:03d}/{total_requests}] seed={master_seed} "
                    f"n={n} C={C} k={k} T={T} f={point.deletion_fraction} "
                    f"r={rows[0]['deletion_size_r']} M_s={rows[0]['M_s']} "
                    f"failures={failures} seconds={time.perf_counter()-start:.2f}",
                    flush=True,
                )
            del checkpoint
            gc.collect()

    expected_rows = len(points) * len(MASTER_SEEDS) * len(METHODS)
    actual_rows = len(_completed_raw_keys(raw_path))
    if actual_rows != expected_rows:
        raise RuntimeError(f"raw result coverage is {actual_rows}/{expected_rows} method rows")
    print(f"[P3 run complete] raw={raw_path} rows={actual_rows} failures={failure_count}", flush=True)


AGGREGATED_ID_FIELDS = (
    "schema_version", "declaration_sha256", "design_index", "selection_reason",
    "dataset_config_id", "acs_task", "acs_survey_year", "natural_client_type",
    "n", "C", "k", "T", "d", "requested_deletion_fraction", "deletion_size_r",
    "realized_deletion_fraction", "method", "expected_seed_count", "observed_seed_count",
    "completed_seed_count", "failed_seed_count", "unavailable_seed_count",
    "missing_seed_count", "contributing_seeds_json", "status_counts_json",
)
AGGREGATE_METRICS = (
    "total_runtime_seconds", "communication_numeric_scalars", "M_s", "margin_mean",
    "margin_median", "center_shift_mean", "center_shift_max", "certificate_pass_rate",
)
AGGREGATED_FIELDS = AGGREGATED_ID_FIELDS + tuple(
    f"{metric}_{summary}"
    for metric in AGGREGATE_METRICS
    for summary in ("mean", "std", "median")
)


def _float_or_none(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _summaries(values: Iterable[Any]) -> tuple[Any, Any, Any]:
    parsed = [value for item in values if (value := _float_or_none(item)) is not None]
    if not parsed:
        return "", "", ""
    array = np.asarray(parsed, dtype=np.float64)
    std = float(np.std(array, ddof=1)) if array.size > 1 else 0.0
    return float(np.mean(array)), std, float(np.median(array))


def load_latest_raw(raw_path: Path) -> list[dict[str, str]]:
    latest: OrderedDict[tuple[int, int, str], dict[str, str]] = OrderedDict()
    for row in _read_csv(raw_path):
        if row.get("declaration_sha256") != DECLARATION_SHA256:
            raise ValueError(f"declaration mismatch in {raw_path}")
        key = (int(row["design_index"]), int(row["master_seed"]), row["method"])
        latest[key] = row
    return list(latest.values())


def aggregate_results(output_dir: Path) -> Path:
    raw = load_latest_raw(output_dir / RAW_NAME)
    grouped: defaultdict[tuple[int, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        grouped[(int(row["design_index"]), row["method"])].append(row)

    output_rows = []
    for point in fractional_design():
        for method in METHODS:
            rows = grouped.get((point.design_index, method), [])
            first = rows[0] if rows else None
            status_counts: defaultdict[str, int] = defaultdict(int)
            for row in rows:
                status_counts[row["status"]] += 1
            completed_rows = [row for row in rows if row["status"] == "complete"]
            observed_seeds = {int(row["master_seed"]) for row in rows}
            completed_seeds = sorted({int(row["master_seed"]) for row in completed_rows})
            failed = sum(count for status, count in status_counts.items() if status not in ("complete", "unavailable"))
            unavailable = status_counts.get("unavailable", 0)
            base = {
                "schema_version": 1,
                "declaration_sha256": DECLARATION_SHA256,
                "design_index": point.design_index,
                "selection_reason": point.selection_reason,
                "dataset_config_id": first["dataset_config_id"] if first else "",
                "acs_task": DECLARATION["acs_task"],
                "acs_survey_year": DECLARATION["acs_survey_year"],
                "natural_client_type": first["natural_client_type"] if first else ("state" if point.C <= 50 else "PUMA"),
                "n": point.n,
                "C": point.C,
                "k": point.k,
                "T": point.T,
                "d": len(FEATURE_NAMES),
                "requested_deletion_fraction": format(point.deletion_fraction, "f"),
                "deletion_size_r": deletion_count(point.n, point.deletion_fraction),
                "realized_deletion_fraction": deletion_count(point.n, point.deletion_fraction) / point.n,
                "method": method,
                "expected_seed_count": len(MASTER_SEEDS),
                "observed_seed_count": len(observed_seeds),
                "completed_seed_count": len(completed_seeds),
                "failed_seed_count": failed,
                "unavailable_seed_count": unavailable,
                "missing_seed_count": len(set(MASTER_SEEDS) - observed_seeds),
                "contributing_seeds_json": _canonical_json(completed_seeds),
                "status_counts_json": _canonical_json(dict(sorted(status_counts.items()))),
            }
            for metric in AGGREGATE_METRICS:
                mean, std, median = _summaries(row[metric] for row in completed_rows)
                base[f"{metric}_mean"] = mean
                base[f"{metric}_std"] = std
                base[f"{metric}_median"] = median
            output_rows.append(base)

    path = output_dir / AGGREGATED_NAME
    _write_csv(path, AGGREGATED_FIELDS, output_rows)
    print(f"wrote {path} ({len(output_rows)} rows)")
    return path


def _aggregate_lookup(output_dir: Path) -> dict[tuple[int, str], dict[str, str]]:
    path = output_dir / AGGREGATED_NAME
    rows = _read_csv(path)
    if any(row.get("declaration_sha256") != DECLARATION_SHA256 for row in rows):
        raise ValueError(f"declaration mismatch in {path}")
    return {(int(row["design_index"]), row["method"]): row for row in rows}


def _factor_sweep(points: Sequence[DesignPoint], factor: str) -> list[DesignPoint]:
    position = {"n": 0, "C": 1, "k": 2, "T": 3, "deletion_fraction": 4}[factor]
    selected = [
        point for point in points
        if all(point.values[index] == REFERENCE[index] for index in range(5) if index != position)
    ]
    return sorted(selected, key=lambda point: float(point.values[position]))


def generate_figure(output_dir: Path) -> Path:
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "p3_mpl_cache"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullFormatter

    lookup = _aggregate_lookup(output_dir)
    points = fractional_design()
    method_styles = {
        "Fresh Retraining": dict(color="#222222", marker="o", linestyle="-"),
        "Direct Full Replay": dict(color="#D55E00", marker="s", linestyle="-"),
        "Basic All-Competitor CertifiedReplay": dict(color="#0072B2", marker="^", linestyle="--"),
        "Runner-Up-Identity CertifiedReplay": dict(color="#009E73", marker="D", linestyle=":"),
    }
    runtime_display_labels = {
        "Fresh Retraining": "Fresh Retraining",
        "Direct Full Replay": "Direct Full Replay",
        "Basic All-Competitor CertifiedReplay": "Basic CertifiedReplay",
        "Runner-Up-Identity CertifiedReplay": "Runner-Up CertifiedReplay",
    }
    certificate_styles = {
        "Basic All-Competitor CertifiedReplay": dict(color="#CC79A7", marker="P", linestyle="--"),
        "Runner-Up-Identity CertifiedReplay": dict(color="#E69F00", marker="X", linestyle=":"),
    }
    certificate_display_labels = {
        "Basic All-Competitor CertifiedReplay": "Basic Certificate",
        "Runner-Up-Identity CertifiedReplay": "Runner-Up Certificate",
    }

    fig, axes = plt.subplots(2, 4, figsize=(18, 8.2))
    panels = axes.ravel()

    def x_values(sweep: Sequence[DesignPoint], factor: str) -> list[float]:
        if factor == "deletion_fraction":
            return [float(point.deletion_fraction) for point in sweep]
        return [float(getattr(point, factor)) for point in sweep]

    def ticks(axis, xs: Sequence[float], factor: str) -> None:
        axis.set_xticks(xs)
        axis.xaxis.set_minor_formatter(NullFormatter())
        if factor == "n":
            axis.set_xticklabels(("100k", "250k", "500k", "1M"))
        elif factor == "deletion_fraction":
            axis.set_xticklabels((r"$10^{-5}$", r"$10^{-4}$", r"$10^{-3}$", r"$10^{-2}$", "0.05"))
        else:
            axis.set_xticklabels([str(int(value)) for value in xs])

    def runtime_panel(axis, factor: str, xlabel: str) -> None:
        sweep = _factor_sweep(points, factor)
        xs = x_values(sweep, factor)
        for method in METHODS:
            means = [float(lookup[(point.design_index, method)]["total_runtime_seconds_mean"]) for point in sweep]
            axis.plot(
                xs,
                means,
                label=runtime_display_labels[method],
                linewidth=1.7,
                markersize=4.5,
                **method_styles[method],
            )
        axis.set_xscale("log")
        axis.set_yscale("log")
        ticks(axis, xs, factor)
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Runtime (seconds)")
        axis.grid(True, which="both", alpha=0.25)

    runtime_panel(panels[0], "n", "Records n")
    runtime_panel(panels[1], "C", "Natural clients C")
    runtime_panel(panels[2], "k", "Clusters k")
    runtime_panel(panels[3], "T", "Refinement rounds T")
    runtime_panel(panels[4], "deletion_fraction", "deletion fraction r/n")

    def certificate_panel(axis, factor: str, xlabel: str) -> None:
        sweep = _factor_sweep(points, factor)
        xs = x_values(sweep, factor)
        for method in CERTIFICATE_LABELS:
            means = [float(lookup[(point.design_index, method)]["certificate_pass_rate_mean"]) for point in sweep]
            stds = [float(lookup[(point.design_index, method)]["certificate_pass_rate_std"]) for point in sweep]
            axis.plot(
                xs,
                means,
                label=certificate_display_labels[method],
                linewidth=1.7,
                markersize=5.5,
                **certificate_styles[method],
            )
            axis.fill_between(
                xs,
                np.maximum(0.0, np.asarray(means) - np.asarray(stds)),
                np.minimum(1.0, np.asarray(means) + np.asarray(stds)),
                color=certificate_styles[method]["color"], alpha=0.10,
            )
        axis.set_xscale("log")
        ticks(axis, xs, factor)
        axis.set_ylim(-0.03, 1.03)
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Certificate pass rate")
        axis.grid(True, which="both", alpha=0.25)

    certificate_panel(panels[5], "deletion_fraction", "deletion fraction r/n")
    certificate_panel(panels[6], "k", "Clusters k")

    k_sweep = _factor_sweep(points, "k")
    xs = x_values(k_sweep, "k")
    margin_means = [
        float(lookup[(point.design_index, "Basic All-Competitor CertifiedReplay")]["margin_mean_mean"])
        for point in k_sweep
    ]
    margin_stds = [
        float(lookup[(point.design_index, "Basic All-Competitor CertifiedReplay")]["margin_mean_std"])
        for point in k_sweep
    ]
    panels[7].plot(xs, margin_means, color="#7F3C8D", marker="o", linewidth=1.7)
    panels[7].fill_between(
        xs,
        np.maximum(0.0, np.asarray(margin_means) - np.asarray(margin_stds)),
        np.asarray(margin_means) + np.asarray(margin_stds),
        color="#7F3C8D", alpha=0.10,
    )
    panels[7].set_xscale("log")
    ticks(panels[7], xs, "k")
    panels[7].set_xlabel("Clusters k")
    panels[7].set_ylabel(r"Mean cached margin $d_2-d_1$")
    panels[7].grid(True, which="both", alpha=0.25)

    titles = (
        "(a) Runtime vs n", "(b) Runtime vs C", "(c) Runtime vs k",
        "(d) Runtime vs T", "(e) Runtime vs deletion fraction",
        "(f) Certificates vs deletion fraction", "(g) Certificates vs k",
        "(h) Cached margin vs k",
    )
    for axis, title in zip(panels, titles):
        axis.set_title(title, fontsize=10.5)

    runtime_handles, runtime_labels = panels[0].get_legend_handles_labels()
    certificate_handles, certificate_names = panels[5].get_legend_handles_labels()
    fig.legend(
        runtime_handles + certificate_handles,
        runtime_labels + certificate_names,
        loc="upper center", bbox_to_anchor=(0.5, 0.946), ncol=3,
        frameon=False, fontsize=9,
    )
    fig.suptitle(
        f"P3 ACS natural federation — {DECLARATION['acs_task']}, {DECLARATION['acs_survey_year']}",
        y=0.995, fontsize=13,
    )
    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.08, top=0.79, wspace=0.30, hspace=0.42)
    path = output_dir / FIGURE_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")
    return path


TABLE_FIELDS = (
    "design_index", "selection_reason", "n", "C", "k", "T",
    "requested_deletion_fraction", "deletion_size_r", "M_s_mean", "M_s_std",
    "margin_mean", "empirical_kappa", "fresh_completed_seeds",
    "direct_completed_seeds", "basic_completed_seeds", "runnerup_completed_seeds",
    "fresh_runtime_seconds_mean", "direct_runtime_seconds_mean",
    "basic_runtime_seconds_mean", "runnerup_runtime_seconds_mean",
    "fresh_communication_numeric_scalars_mean", "direct_communication_numeric_scalars_mean",
    "basic_communication_numeric_scalars_mean", "runnerup_communication_numeric_scalars_mean",
    "basic_certificate_pass_rate_mean", "runnerup_certificate_pass_rate_mean",
)


def generate_compact_table(output_dir: Path) -> Path:
    lookup = _aggregate_lookup(output_dir)
    diagnostics = _read_csv(output_dir / DIAGNOSTICS_NAME)
    kappa_by_dataset = {row["dataset_config_id"]: row["empirical_kappa"] for row in diagnostics}
    output_rows = []
    short = {
        "Fresh Retraining": "fresh",
        "Direct Full Replay": "direct",
        "Basic All-Competitor CertifiedReplay": "basic",
        "Runner-Up-Identity CertifiedReplay": "runnerup",
    }
    for point in fractional_design():
        rows = {method: lookup[(point.design_index, method)] for method in METHODS}
        fresh = rows["Fresh Retraining"]
        basic = rows["Basic All-Competitor CertifiedReplay"]
        output: dict[str, Any] = {
            "design_index": point.design_index,
            "selection_reason": point.selection_reason,
            "n": point.n,
            "C": point.C,
            "k": point.k,
            "T": point.T,
            "requested_deletion_fraction": format(point.deletion_fraction, "f"),
            "deletion_size_r": deletion_count(point.n, point.deletion_fraction),
            "M_s_mean": fresh["M_s_mean"],
            "M_s_std": fresh["M_s_std"],
            "margin_mean": basic["margin_mean_mean"],
            "empirical_kappa": kappa_by_dataset[fresh["dataset_config_id"]],
            "basic_certificate_pass_rate_mean": basic["certificate_pass_rate_mean"],
            "runnerup_certificate_pass_rate_mean": rows[
                "Runner-Up-Identity CertifiedReplay"
            ]["certificate_pass_rate_mean"],
        }
        for method, label in short.items():
            output[f"{label}_completed_seeds"] = rows[method]["completed_seed_count"]
            output[f"{label}_runtime_seconds_mean"] = rows[method]["total_runtime_seconds_mean"]
            output[f"{label}_communication_numeric_scalars_mean"] = rows[method][
                "communication_numeric_scalars_mean"
            ]
        output_rows.append(output)
    path = output_dir / TABLE_NAME
    _write_csv(path, TABLE_FIELDS, output_rows)
    print(f"wrote {path} ({len(output_rows)} rows)")
    return path


def _fmt(value: Any, digits: int = 4) -> str:
    parsed = _float_or_none(value)
    if parsed is None:
        return "NA"
    return f"{parsed:.{digits}g}"


def generate_report(output_dir: Path) -> Path:
    predeclared = _read_csv(output_dir / PREDECLARATION_NAME)[0]
    diagnostics = _read_csv(output_dir / DIAGNOSTICS_NAME)
    aggregate = _read_csv(output_dir / AGGREGATED_NAME)
    systems = _read_csv(output_dir / TABLE_NAME)
    lookup = {(int(row["design_index"]), row["method"]): row for row in aggregate}

    diagnostic_groups: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in diagnostics:
        diagnostic_groups[row["dataset_config_id"]].append(row)

    lines = [
        "# P3. ACS/Folktables Natural Federation",
        "",
        "This report was generated only from the saved P3 CSV files; report generation did not run training or replay.",
        "",
        "## Experiment declaration",
        "",
        f"- ACS task and year: `{predeclared['acs_task']}`, {predeclared['acs_survey_year']} `{predeclared['acs_horizon']}` `{predeclared['acs_survey']}` survey.",
        f"- Geographic filters: {predeclared['geographic_filters_json']}.",
        f"- Clustering features: {predeclared['feature_columns_json']}.",
        f"- Missing values: {predeclared['missing_value_rule']}.",
        f"- Categorical encoding: {predeclared['categorical_encoding_rule']}.",
        f"- Standardization: {predeclared['standardization_rule']}.",
        f"- Groups: {predeclared['two_group_definition']}.",
        f"- Natural-client selection: {predeclared['natural_client_selection_rule']}.",
        f"- Record subsampling: {predeclared['record_subsampling_rule']}.",
        f"- Uniform deletion sampling: {predeclared['deletion_sampling_rule']}.",
        f"- Nearly-pure threshold: {predeclared['nearly_pure_threshold']} (strictly pure clients are excluded from nearly-pure status).",
        f"- Final feature dimension: d={len(FEATURE_NAMES)}.",
        f"- Master seeds: {predeclared['master_seeds_json']}.",
        f"- Frozen declaration SHA-256: `{predeclared['declaration_sha256']}`.",
        "",
        "## Natural federation diagnostics",
        "",
        f"Complete per-client counts, proportions, kappa components, slice status, and per-feature means/standard deviations are in [{DIAGNOSTICS_NAME}]({DIAGNOSTICS_NAME}).",
        "",
    ]

    def diagnostic_sort(item: tuple[str, list[dict[str, str]]]) -> tuple[int, int]:
        rows = item[1]
        return int(rows[0]["n"]), int(rows[0]["C"])

    for _, rows in sorted(diagnostic_groups.items(), key=diagnostic_sort):
        first = rows[0]
        sizes = np.asarray([float(row["client_size"]) for row in rows])
        props = np.asarray([float(row["group_A_proportion"]) for row in rows])
        empty_slices = sum(
            row["group_A_slice_empty"] == "True" or row["group_B_slice_empty"] == "True"
            for row in rows
        )
        mean_spreads = {
            feature: max(float(row[f"feature_mean_{feature}"]) for row in rows)
            - min(float(row[f"feature_mean_{feature}"]) for row in rows)
            for feature in FEATURE_NAMES
        }
        std_spreads = {
            feature: max(float(row[f"feature_std_{feature}"]) for row in rows)
            - min(float(row[f"feature_std_{feature}"]) for row in rows)
            for feature in FEATURE_NAMES
        }
        max_mean_feature = max(mean_spreads, key=mean_spreads.get)
        max_std_feature = max(std_spreads, key=std_spreads.get)
        lines.append(
            f"- n={first['n']}, C={first['C']} ({first['natural_client_type']}): client sizes "
            f"min/median/max={int(np.min(sizes))}/{_fmt(np.median(sizes))}/{int(np.max(sizes))}; "
            f"Group-A proportions min/median/max={_fmt(np.min(props))}/{_fmt(np.median(props))}/{_fmt(np.max(props))}; "
            f"empirical kappa={_fmt(first['empirical_kappa'])}; pure={first['pure_client_count']}, "
            f"nearly pure={first['nearly_pure_client_count']}, clients with an empty slice={empty_slices}; "
            f"largest across-client feature-mean range is {max_mean_feature}={_fmt(mean_spreads[max_mean_feature])}, "
            f"and largest across-client feature-std range is {max_std_feature}={_fmt(std_spreads[max_std_feature])}."
        )

    lines.extend(
        [
            "",
            "Pure clients contribute factor one to empirical kappa exactly as declared. Geographic shift is reported from the stored means and standard deviations in the final clustering feature space; no additional distribution distance was introduced.",
            "",
            "## Experimental configuration",
            "",
            f"The compute-adjusted fractional design contains {len(fractional_design())} configurations. Its intercept plus reference-coded categorical main-effects matrix has rank {DESIGN_VALIDATION['rank']} of {len(DESIGN_VALIDATION['columns'])}; the r–M_s, k–margin, and C–communication sweep matrices each have rank 2.",
            "",
        ]
    )
    for point in fractional_design():
        r = deletion_count(point.n, point.deletion_fraction)
        lines.append(
            f"- design {point.design_index}: n={point.n}, C={point.C}, k={point.k}, "
            f"T={point.T}, requested r/n={point.deletion_fraction}, r={r} ({point.selection_reason})."
        )

    all_completed = [int(row["completed_seed_count"]) for row in aggregate]
    all_failed = sum(int(row["failed_seed_count"]) for row in aggregate)
    all_missing = sum(int(row["missing_seed_count"]) for row in aggregate)
    lines.extend(
        [
            "",
            "## Five-seed results",
            "",
            f"Every aggregate records its contributing seed count. Across the 19 configurations and four methods, completed-seed counts range from {min(all_completed)} to {max(all_completed)} of 5; failed method-seeds={all_failed}; missing method-seeds={all_missing}. Raw seed-level rows remain in [raw_results.csv](raw_results.csv).",
            "",
            "## Four-method runtime comparison",
            "",
        ]
    )
    reference_point = fractional_design()[0]
    for method in METHODS:
        row = lookup[(reference_point.design_index, method)]
        lines.append(
            f"- {method}: mean={_fmt(row['total_runtime_seconds_mean'])} s, "
            f"std={_fmt(row['total_runtime_seconds_std'])} s, median={_fmt(row['total_runtime_seconds_median'])} s; "
            f"successful seeds={row['completed_seed_count']}/5."
        )

    lines.extend(["", "## Certificate behavior", ""])
    for method, label in CERTIFICATE_LABELS.items():
        row = lookup[(reference_point.design_index, method)]
        lines.append(
            f"- {label}: pass-rate mean={_fmt(row['certificate_pass_rate_mean'])}, "
            f"std={_fmt(row['certificate_pass_rate_std'])}, median={_fmt(row['certificate_pass_rate_median'])}; "
            f"successful seeds={row['completed_seed_count']}/5."
        )
    lines.append("Fresh Retraining and Direct Full Replay have no certificate pass-rate values in the raw or aggregated CSV.")

    lines.extend(["", "## Required P3 relationships", "", "### Deletion size and touched-slice mass", ""])
    for point in _factor_sweep(fractional_design(), "deletion_fraction"):
        row = lookup[(point.design_index, "Fresh Retraining")]
        lines.append(
            f"- requested r/n={point.deletion_fraction}, r={deletion_count(point.n, point.deletion_fraction)}: "
            f"M_s mean/std/median={_fmt(row['M_s_mean'])}/{_fmt(row['M_s_std'])}/{_fmt(row['M_s_median'])}."
        )

    lines.extend(["", "### Cluster count, cached margin, and certificate pass rate", ""])
    for point in _factor_sweep(fractional_design(), "k"):
        basic = lookup[(point.design_index, "Basic All-Competitor CertifiedReplay")]
        runner = lookup[(point.design_index, "Runner-Up-Identity CertifiedReplay")]
        lines.append(
            f"- k={point.k}: retained cached margin mean={_fmt(basic['margin_mean_mean'])}; "
            f"basic pass={_fmt(basic['certificate_pass_rate_mean'])}; "
            f"runner-up pass={_fmt(runner['certificate_pass_rate_mean'])}."
        )

    lines.extend(["", "### Natural-client count and communication", ""])
    systems_by_index = {int(row["design_index"]): row for row in systems}
    for point in _factor_sweep(fractional_design(), "C"):
        row = systems_by_index[point.design_index]
        lines.append(
            f"- C={point.C} ({'state' if point.C <= 50 else 'PUMA'}): communication numeric scalars "
            f"Fresh/Direct/Basic/Runner-Up={_fmt(row['fresh_communication_numeric_scalars_mean'])}/"
            f"{_fmt(row['direct_communication_numeric_scalars_mean'])}/"
            f"{_fmt(row['basic_communication_numeric_scalars_mean'])}/"
            f"{_fmt(row['runnerup_communication_numeric_scalars_mean'])}."
        )
    lines.extend(
        [
            "",
            f"The baseline contains no serialized-byte meter, so communication uses only the minimal existing-path scalar counter declared before execution: {COMMUNICATION_RULE}",
            "",
            "## Main-paper outputs",
            "",
            f"- ACS scaling/certificate figure: [{FIGURE_NAME}]({FIGURE_NAME}).",
            f"- Compact systems table: [{TABLE_NAME}]({TABLE_NAME}).",
            f"- Aggregated five-seed results: [{AGGREGATED_NAME}]({AGGREGATED_NAME}).",
        ]
    )
    path = output_dir / REPORT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run the complete 19-point P3 design for all five seeds")
    run_parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    run_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    run_parser.add_argument("--download", action="store_true")
    run_parser.add_argument("--resume", action="store_true")

    for command, help_text in (
        ("aggregate", "regenerate aggregated_results.csv from raw_results.csv"),
        ("plot", "regenerate the one ACS scaling/certificate figure"),
        ("table", "regenerate the one compact systems table"),
        ("report", "regenerate report.md from saved CSV files"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        run_experiment(args.data_dir, args.output_dir, args.download, args.resume)
        # Each function below reloads saved CSVs.  They remain separately
        # invocable and do not receive in-memory training results.
        aggregate_results(args.output_dir)
        generate_figure(args.output_dir)
        generate_compact_table(args.output_dir)
        generate_report(args.output_dir)
        return 0
    if args.command == "aggregate":
        aggregate_results(args.output_dir)
    elif args.command == "plot":
        generate_figure(args.output_dir)
    elif args.command == "table":
        generate_compact_table(args.output_dir)
    elif args.command == "report":
        generate_report(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit("Reference helper driver only. Execute corrected gated runs with: python remediation/scripts/run_experiments.py --stages P3 --run-id corrected-v1")
