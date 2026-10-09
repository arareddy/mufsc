"""One process per map execution; oracle mode imports no production modules."""
import argparse
import json
import os
import pickle
import sys
from pathlib import Path

from rational_oracle import hex_centers, training

parser = argparse.ArgumentParser()
parser.add_argument("--case", required=True)
parser.add_argument("--mode", required=True, choices=["checkpoint", "fresh", "oracle", "none", "basic", "runnerup"])
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
spec = json.loads(Path(args.case).read_text())
data = {int(c): x for c, x in spec["data"].items()}
groups = {int(c): g for c, g in spec["groups"].items()}
removed = {int(c): r for c, r in spec["removed"].items()}
retained = {c: [x for i, x in enumerate(points) if i not in removed.get(c, [])] for c, points in data.items()}
retained_groups = {c: [g for i, g in enumerate(values) if i not in removed.get(c, [])] for c, values in groups.items()}
parameters = spec["parameters"]
if args.mode == "oracle":
    result = training(retained, retained_groups, **parameters)
else:
    import numpy as np
    sys.dont_write_bytecode = True
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "core" / "src"))
    from fixedpoint import FixedPointConfig
    from train import train_full
    from unlearn import unlearn
    kwargs = {key: value for key, value in parameters.items() if key not in ["bits", "clip"]}
    kwargs["fp_cfg"] = FixedPointConfig(parameters["bits"], parameters["clip"])
    d = len(next(x for x in data.values() if x)[0])
    if args.mode in ["checkpoint", "fresh"]:
        cd, go = (data, groups) if args.mode == "checkpoint" else (retained, retained_groups)
        actual = train_full({c: np.array(x, dtype=float).reshape(-1, d) for c, x in reversed(list(cd.items()))},
                            {c: np.array(g, dtype=np.int64) for c, g in go.items()}, **kwargs)
        if args.mode == "checkpoint":
            Path(args.checkpoint).write_bytes(pickle.dumps(actual, protocol=5))
    else:
        actual = pickle.loads(Path(args.checkpoint).read_bytes())
        actual = unlearn(actual, {c: np.array(r, dtype=np.int64) for c, r in reversed(list(removed.items()))}, args.mode)
    result = {"trajectory": [hex_centers(c) for c in actual["trajectory"]],
              "per_round_stats": actual["per_round_stats"],
              "slices": {f"{c}:{g}": {"selected_idx": res["selected_idx"].tolist(),
                       "mult": res["mult"].tolist(), "anchors": hex_centers(res["anchors"])}
                         for (c, g), res in actual["slice_results"].items()},
              "cache_valid": actual["cache_valid"], "digests": actual["digests"],
              "diagnostics": actual.get("diagnostics", [])}
result["process"] = {"pid": os.getpid(), "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"), "mode": args.mode}
Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
