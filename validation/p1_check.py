"""Independently gate P1's run-length evaluator against literal per-record arrays.

This uses full literal records, not block sums, in both an independent
Fraction sampler and the canonical production sampler. Every local/server
index, multiplicity, exact weight, and raw word count must agree.
"""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'oracle'))
from rational_oracle import categorical, hex_centers, tape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "historical/p1_p4/src"))
sys.path.insert(0, str(ROOT / "historical/p1_p4/experiments"))
from kmeanspp import weighted_kmeanspp
from p1_compressed import compressed_seed


class CountWords:
    def __init__(self, seed, role, *entities):
        self.generator = tape(seed, role, *entities)
        self.bit_generator = self
        self.words = 0
    def random_raw(self):
        self.words += 1
        return self.generator.bit_generator.random_raw()


def literal_oracle_sample(values, weights, k, random):
    n = len(values)
    if k >= n:
        return list(range(n)) + [i % n for i in range(k - n)]
    if sum(weights) == 0:
        return list(range(k))
    chosen = [categorical(weights, random)]
    while len(chosen) < k:
        masses = [w * min((x - values[j]) ** 2 for j in chosen) for x, w in zip(values, weights)]
        if not any(masses):
            break
        chosen.append(categorical(masses, random))
    for i in range(n):
        if len(chosen) == k:
            break
        if i not in chosen:
            chosen.append(i)
    return chosen


def literal_production_sample(values, weights, k, random):
    return weighted_kmeanspp(np.array(values, dtype=float).reshape(-1, 1), weights, k, random).tolist()


def literal_seed(kappa, seed, method, sample):
    # Materialize every physical record in the analytic UNIT150 witness.
    n = (kappa + 1) * 150
    data = {0: [0] * (kappa * 150) + [10] * 150,
            1: [0] * 150 + [0] * (kappa * 150)}
    groups = {0: [0] * (kappa * 150) + [1] * 150,
              1: [0] * 150 + [1] * (kappa * 150)}
    trace, anchors, server_weights = {}, [], []
    if method == "centralized":
        values = data[0] + data[1]
        random = CountWords(seed, "centralized")
        selected = sample(values, [Fraction(1, n)] * len(values), 1, random)
        trace["centralized"] = {"selected_idx": selected, "raw_words": random.words}
        return [[values[selected[0]]]], trace
    if method == "splitgroup_2k":
        for c in range(2):
            for g in range(2):
                values = [v for v, group in zip(data[c], groups[c]) if group == g]
                random = CountWords(seed, "local", c, g)
                selected = sample(values, [Fraction(1)] * len(values), 1, random)
                reps = [values[i] for i in selected]
                labels = [min(range(len(reps)), key=lambda j: ((x - reps[j]) ** 2, j)) for x in values]
                mult = [labels.count(j) for j in range(len(reps))]
                anchors.extend([[rep] for rep in reps])
                server_weights.extend(Fraction(m, n) for m in mult)
                trace[f"local:{c}:{g}"] = {"selected_idx": selected, "raw_words": random.words, "mult": mult}
        role = "server"
    else:
        budget = 1 if method == "merged_1k" else 2
        for c in range(2):
            counts = [groups[c].count(0), groups[c].count(1)]
            weights = [Fraction(1, counts[g]) for g in groups[c]]
            random = CountWords(seed, "merged_local", c)
            selected = sample(data[c], weights, budget, random)
            reps = [data[c][i] for i in selected]
            labels = [min(range(budget), key=lambda j: ((x - reps[j]) ** 2, j)) for x in data[c]]
            h = [[sum(g == group and label == j for g, label in zip(groups[c], labels))
                  for j in range(budget)] for group in range(2)]
            trace[f"merged_local:{c}"] = {"selected_idx": selected, "raw_words": random.words,
                                           "h_A": h[0], "h_B": h[1]}
            anchors.extend([[v] for v in reps])
            server_weights.extend(Fraction(h[0][j] + h[1][j], n) for j in range(budget))
        role = "merged_server"
    random = CountWords(seed, role)
    selected = sample([a[0] for a in anchors], server_weights, 1, random)
    trace[role] = {"selected_idx": selected, "raw_words": random.words, "anchors": anchors,
                   "weights": list(map(str, server_weights))}
    return [anchors[i] for i in selected], trace



if __name__=='__main__':
    cases=0
    for kappa in [1,2,4,8,16,32,64,128]:
        for method in ['merged_1k','merged_2k','splitgroup_2k','centralized']:
            for seed in [0,1,19]:
                expected,trace=literal_seed(kappa,seed,method,literal_oracle_sample)
                actual,production_trace=literal_seed(kappa,seed,method,literal_production_sample)
                compressed,compressed_trace=compressed_seed(kappa,seed,method)
                assert hex_centers(actual)==hex_centers(expected)==hex_centers(compressed)
                assert production_trace==trace==compressed_trace
                cases+=1
    print(json.dumps({'status':'PASS','literal_P1_cases':cases,'historical_source':True}))
