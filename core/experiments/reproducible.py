"""Reproducible experiment I/O. No training arithmetic lives in this module."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from datetime import datetime, timezone
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
REMEDIATION = ROOT / "remediation"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(value):
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "numerator") and hasattr(value, "denominator") and not isinstance(value, (int, float)):
        return {"numerator": int(value.numerator), "denominator": int(value.denominator)}
    return value


def canonical(value):
    return json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_json(path, value, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if immutable and path.exists():
        if path.read_bytes() != encoded:
            raise RuntimeError(f"refusing to overwrite immutable artifact {path}")
        return
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def source_manifest():
    files = sorted((PROJECT / "src").glob("*.py"))
    paths = {str(p.relative_to(PROJECT)): sha256(p) for p in files}
    return dict(files=paths, code_sha256=content_hash(paths), map_sha256=sha256(PROJECT / "TRAINING_MAP.md"))


def environment_manifest():
    return dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                machine=platform.machine(), numpy=np.__version__,
                thread_settings={k: os.environ.get(k) for k in (
                    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})


def require_gate(path=None):
    gate_path = Path(path or REMEDIATION / "evidence" / "corrected_map_gate.json")
    if not gate_path.exists():
        raise RuntimeError(f"corrected-map gate is absent: {gate_path}; experiments are not authorized to start before it passes")
    gate = json.loads(gate_path.read_text())
    if str(gate.get("status", "")).upper() != "PASS":
        raise RuntimeError("corrected-map gate is not PASS")
    current = source_manifest()
    for key in ("code_sha256", "map_sha256"):
        if gate.get(key) != current[key]:
            raise RuntimeError(f"corrected-map gate is stale for {key}; revalidate affected behavior")
    return dict(path=str(gate_path), sha256=sha256(gate_path), **current)


def array_witness(value):
    a = np.ascontiguousarray(value, dtype="<f8")
    return dict(shape=list(a.shape), dtype="<f8", bytes_hex=a.tobytes().hex(),
                values_hex=[float(v).hex() for v in a.ravel()])


def exact_witness(result):
    """Persist indexed center bytes and every exact integer N/S/SS value."""
    stats = result.get("per_round_stats")
    trajectory = result.get("trajectory")
    if trajectory is None or stats is None:
        raise RuntimeError("kernel did not return full trajectory and per_round_stats")
    def integers(a):
        if isinstance(a, (list, tuple, np.ndarray)):
            return [integers(v) for v in a]
        if not isinstance(a, (int, np.integer)):
            raise TypeError(f"noninteger statistic {type(a)}")
        return int(a)
    return dict(trajectory=[array_witness(c) for c in trajectory],
                final_centers=array_witness(result["final_centers"]),
                per_round_stats=[dict(zip(("N", "S", "SS"), (integers(a) for a in row))) for row in stats])


def now():
    return datetime.now(timezone.utc).isoformat()
