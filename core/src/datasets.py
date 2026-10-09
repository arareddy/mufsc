"""Fixed-artifact P2/P4 loader, dataset contract version 2.

Select only exact ``client_<integer>`` data keys, once per source client.
The deletion identity is (processed-artifact SHA256, source client, source
local row); verified full_data row indices are also returned. Preprocessing
was fitted before these supplied artifacts. Its influence is outside the
fixed-representation deletion target; no public/disjoint-fit claim is made.
Only load trusted local benchmark pickles, never an untrusted upload.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import pickle
import re
import numpy as np

DATASET_VERSION = "p124-unique-source-v2"
DATASET_FILES = {
    "adult": ("adult_processed_final.pkl", "male_mask", 100),
    "bank": ("bank_20clients_processed_final.pkl", "married_mask", 20),
    "credit": ("credit_processed_final.pkl", "higher_edu_mask", 100),
}


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _binary_mask(value, n, name):
    a = np.asarray(value)
    if a.shape != (n,) or not np.all((a == 0) | (a == 1)):
        raise ValueError(f"{name}: expected a length-{n} binary mask")
    return np.ascontiguousarray(a, dtype=bool)


def reconstructed_source_rows(raw, mask_key, source_ids):
    """Replay the supplied seed42 stratified split; verify every ordered byte.

    This yields indices in the supplied full_data artifact, not an invented
    upstream UCI native ID. The deterministic partition distinguishes duplicate
    rows by full_data position and is verified against all source client arrays.
    """
    if source_ids != list(range(len(source_ids))):
        raise ValueError("source client IDs must be the contiguous frozen partition")
    full = np.asarray(raw["full_data"], dtype=np.float64)
    if full.ndim != 2 or not np.isfinite(full).all():
        raise ValueError("full_data must be a finite matrix")
    mask = _binary_mask(raw[f"full_{mask_key}"], len(full), f"full_{mask_key}")
    rng = np.random.default_rng(42)
    yes = rng.permutation(np.flatnonzero(mask))
    no = rng.permutation(np.flatnonzero(~mask))
    C = len(source_ids)
    if not C:
        raise ValueError("no source clients")
    sizes = len(yes) // C, len(no) // C
    mapping = {}
    for c in source_ids:
        a = yes[c * sizes[0] : (c + 1) * sizes[0]] if c < C - 1 else yes[c * sizes[0] :]
        b = no[c * sizes[1] : (c + 1) * sizes[1]] if c < C - 1 else no[c * sizes[1] :]
        rows = np.ascontiguousarray(rng.permutation(np.concatenate((a, b))), dtype=np.int64)
        observed = np.asarray(raw[f"client_{c}"], dtype=np.float64)
        observed_mask = _binary_mask(raw[f"client_{c}_{mask_key}"], len(rows), f"client_{c}_{mask_key}")
        expected = np.ascontiguousarray(full[rows], dtype=np.float64)
        if observed.shape != expected.shape or np.ascontiguousarray(observed).tobytes() != expected.tobytes():
            raise ValueError(f"source client {c}: frozen full_data row reconstruction mismatch")
        if observed_mask.tobytes() != mask[rows].tobytes():
            raise ValueError(f"source client {c}: frozen group reconstruction mismatch")
        mapping[c] = rows
    partition = np.concatenate(list(mapping.values()))
    if not np.array_equal(np.sort(partition), np.arange(len(full))):
        raise ValueError("reconstructed source rows do not partition full_data")
    return mapping


def load_dataset(name: str, data_dir: str, seed: int = 0) -> tuple:
    """Return (client_data, group_of, provenance-rich meta), before map encoding.

    ``meta['source_record_ids'][c]`` is full_data row position for each local
    record, and ``source_client_ids`` maps dense run clients to unique source
    clients. Both remain unchanged when retained rows are sliced. Clipping is
    declared once from this fixed full population and never refitted on deletion.
    """
    if name not in DATASET_FILES:
        raise ValueError(f"unknown dataset {name!r}; choose from {sorted(DATASET_FILES)}")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("dataset seed must be a nonnegative integer")
    fname, mask_key, num_clients_use = DATASET_FILES[name]
    path = Path(data_dir) / fname
    with path.open("rb") as stream:
        raw = pickle.load(stream)
    if not isinstance(raw, dict):
        raise ValueError("processed dataset must be a mapping")
    all_ids = sorted(int(m.group(1)) for key in raw
                     if isinstance(key, str) and (m := re.fullmatch(r"client_(0|[1-9][0-9]*)", key)))
    if len(all_ids) < num_clients_use:
        raise ValueError(f"expected at least {num_clients_use} distinct source clients, got {len(all_ids)}")
    chosen = sorted(np.random.default_rng(int(seed)).choice(
        np.asarray(all_ids, dtype=np.int64), size=num_clients_use, replace=False).tolist())
    if len(set(chosen)) != len(chosen):
        raise AssertionError("duplicate source client selection")
    rows = reconstructed_source_rows(raw, mask_key, all_ids)
    client_data, group_of, source_clients, source_records = {}, {}, {}, {}
    global_max = 0.0
    d = None
    for new_c, old_c in enumerate(chosen):
        X = np.ascontiguousarray(raw[f"client_{old_c}"], dtype=np.float64)
        if X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0 or not np.isfinite(X).all():
            raise ValueError(f"client {old_c}: expected nonempty finite feature matrix")
        if d is None:
            d = X.shape[1]
        if X.shape[1] != d:
            raise ValueError("inconsistent feature dimension")
        groups = _binary_mask(raw[f"client_{old_c}_{mask_key}"], len(X), f"client_{old_c}_{mask_key}")
        client_data[new_c], group_of[new_c] = X, groups.astype(np.int64)
        source_clients[new_c], source_records[new_c] = old_c, rows[old_c].copy()
        global_max = max(global_max, float(np.max(np.abs(X))))
    n_total = sum(len(X) for X in client_data.values())
    group_counts = {g: sum(int(np.sum(y == g)) for y in group_of.values()) for g in (0, 1)}
    if min(group_counts.values()) == 0:
        raise ValueError("each global binary group must be nonempty")
    meta = dict(name=name, version=DATASET_VERSION, num_clients=len(chosen),
                n_total=n_total, d=d, clip=float(np.ceil(global_max)) + 1.0,
                source_file=str(path.resolve()), source_sha256=file_sha256(path),
                selection_seed=int(seed), source_client_ids=source_clients,
                source_record_ids=source_records, group_counts=group_counts,
                source_record_id_scope="zero-based row of immutable processed full_data; verified seed42 partition",
                preprocessing_scope="fixed supplied artifact; no refit; upstream fitted transforms not supplied")
    return client_data, group_of, meta


def removal_identities(meta: dict, removed: dict) -> list[dict]:
    """Canonical native/source identity records for a validated local request."""
    records = []
    for c in sorted(removed):
        if c not in meta["source_client_ids"]:
            raise ValueError(f"unknown client {c}")
        indices = np.asarray(removed[c])
        if indices.ndim != 1 or (indices.size and indices.dtype.kind not in "iu"):
            raise ValueError("deletion indices must be a one-dimensional integer array")
        indices = [int(i) for i in indices]
        if len(set(indices)) != len(indices):
            raise ValueError("duplicate deletion identity")
        for i in sorted(indices):
            if not 0 <= i < len(meta["source_record_ids"][c]):
                raise ValueError("deletion index outside source client")
            full_row = int(meta["source_record_ids"][c][i])
            records.append(dict(client_id=int(c), local_row=i,
                                source_client_id=int(meta["source_client_ids"][c]),
                                processed_full_row=full_row,
                                stable_record_id=f"{meta['source_sha256']}:full-row:{full_row}"))
    return records
