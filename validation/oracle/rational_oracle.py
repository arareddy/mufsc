"""Small, intentionally slow independent oracle for represented-map arithmetic.

No production modules are imported. Inputs are Python sequences. This code
does not certify production results by rerunning production arithmetic: it
uses Fraction throughout and constructs integer aggregates point by point.
"""
from fractions import Fraction
from functools import reduce
from math import gcd, lcm


def rational(x):
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    return Fraction.from_float(float(x))


def squared_distance(a, b):
    return sum((rational(x) - rational(y)) ** 2 for x, y in zip(a, b))


def assignment(points, centers):
    if not centers:
        raise ValueError("at least one indexed center is required")
    order = [sorted(range(len(centers)), key=lambda j: (squared_distance(x, centers[j]), j))
             for x in points]
    return [ids[0] for ids in order], [ids[1] if len(ids) > 1 else -1 for ids in order]


def encode(points, scale_bits, clip):
    """Clip exact represented binary64 inputs, then nearest-even grid round."""
    scale, bound = 2 ** scale_bits, rational(clip)
    return [[round(min(bound, max(-bound, rational(v))) * scale) for v in row]
            for row in points]


def stats(integer_points, groups, labels, k, d=None):
    if d is None:
        d = len(integer_points[0]) if integer_points else 0
    N = [[0 for _ in range(k)] for _ in range(2)]
    S = [[[0 for _ in range(d)] for _ in range(k)] for _ in range(2)]
    SS = [[0 for _ in range(k)] for _ in range(2)]
    for x, g, j in zip(integer_points, groups, labels):
        g, j = int(g), int(j)
        N[g][j] += 1
        SS[g][j] += sum(int(v) ** 2 for v in x)
        for h, v in enumerate(x):
            S[g][j][h] += int(v)
    return N, S, SS


def group_objectives(centers, N, S, SS, group_sizes, scale):
    values = []
    for g in range(2):
        total = Fraction(0)
        for j, row in enumerate(centers):
            c = list(map(rational, row))
            total += Fraction(SS[g][j], scale ** 2)
            total -= sum(2 * v * Fraction(s, scale) for v, s in zip(c, S[g][j]))
            total += N[g][j] * sum(v * v for v in c)
        if group_sizes[g] <= 0:
            raise ValueError("both global groups must remain nonempty")
        values.append(total / group_sizes[g])
    return tuple(values)


def candidate(centers, N, S, group_sizes, scale, lam):
    """Exact cell formula with one final binary64 round per coordinate."""
    lam = rational(lam)
    result = []
    for j, old in enumerate(centers):
        na, nb = N[0][j], N[1][j]
        if na == 0 and nb == 0:
            result.append(list(map(float, old)))
            continue
        if na == 0 or nb == 0:
            g = 0 if na else 1
            result.append([float(Fraction(s, N[g][j] * scale)) for s in S[g][j]])
            continue
        a = lam / group_sizes[0]
        b = (1 - lam) / group_sizes[1]
        denom = (a * na + b * nb) * scale
        if denom == 0:
            result.append(list(map(float, old)))
        else:
            result.append([float((a * sa + b * sb) / denom)
                           for sa, sb in zip(S[0][j], S[1][j])])
    return result


def fair_update(centers, N, S, SS, group_sizes, scale, L):
    candidates = {Fraction(0): candidate(centers, N, S, group_sizes, scale, 0),
                  Fraction(1): candidate(centers, N, S, group_sizes, scale, 1)}
    lo, hi = Fraction(0), Fraction(1)
    branches = []
    for _ in range(L):
        lam = (lo + hi) / 2
        c = candidate(centers, N, S, group_sizes, scale, lam)
        candidates[lam] = c
        fa, fb = group_objectives(c, N, S, SS, group_sizes, scale)
        branches.append({"lambda": str(lam), "f_A": str(fa), "f_B": str(fb),
                         "branch": "lo" if fa > fb else "hi"})
        if fa > fb:
            lo = lam
        else:
            hi = lam
    best_lam = min(candidates, key=lambda lam: (
        max(group_objectives(candidates[lam], N, S, SS, group_sizes, scale)), lam))
    chosen = candidates[best_lam]
    accepted = max(group_objectives(chosen, N, S, SS, group_sizes, scale)) <= max(
        group_objectives(centers, N, S, SS, group_sizes, scale))
    return (chosen if accepted else [list(map(float, c)) for c in centers],
            {"lambda": float(best_lam) if accepted else None,
             "accepted": accepted, "branches": branches})


def hex_centers(centers):
    return [[float(v).hex() for v in row] for row in centers]


def random_below(total, generator):
    """Independent reference for the declared whole-word rejection protocol."""
    if total < 1:
        raise ValueError("positive total required")
    bit_count = (total - 1).bit_length()
    if bit_count == 0:
        return 0
    while True:
        value = 0
        for offset in range(0, bit_count, 64):
            value |= int(generator.bit_generator.random_raw()) << offset
        value &= (1 << bit_count) - 1
        if value < total:
            return value


def categorical(masses, generator):
    masses = list(map(rational, masses))
    if not masses or any(v < 0 for v in masses) or sum(masses) <= 0:
        raise ValueError("nonnegative masses of positive total required")
    denom = lcm(*(v.denominator for v in masses))
    integers = [v.numerator * (denom // v.denominator) for v in masses]
    common = reduce(gcd, integers)
    integers = [v // common for v in integers]
    value = random_below(sum(integers), generator)
    for i, w in enumerate(integers):
        if value < w:
            return i
        value -= w
    raise AssertionError("unreachable inverse CDF remainder")


def seed_indices(points, weights, k, generator):
    n = len(points)
    if k == 0:
        return []
    if n == 0:
        raise ValueError("cannot seed an empty population")
    def complete(chosen):
        chosen = list(chosen)
        chosen.extend(i for i in range(n) if i not in chosen)
        while len(chosen) < k:
            chosen.extend(range(n))
        return chosen[:k]
    if k >= n:
        return complete(list(range(n)))
    if sum(weights) == 0:
        return complete([])
    chosen = [categorical(weights, generator)]
    while len(chosen) < k:
        masses = [rational(w) * min(squared_distance(x, points[j]) for j in chosen)
                  for x, w in zip(points, weights)]
        if not any(masses):
            return complete(chosen)
        chosen.append(categorical(masses, generator))
    return chosen


def tape(seed, role, *entities):
    # NumPy is used only as the explicitly declared deterministic PRNG source.
    # It supplies no oracle assignment/objective/update arithmetic.
    import numpy as np
    roles = {"local": 1, "server": 2, "merged_local": 3, "merged_server": 4, "centralized": 5}
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, roles[role], *entities])))


def initialize(client_data, group_of, seed, k, gamma=0., anchor_lloyd_iters=0):
    sizes = [sum(list(groups).count(g) for groups in group_of.values()) for g in range(2)]
    anchors, weights, slices = [], [], {}
    for c in sorted(client_data):
        for g in range(2):
            X = [x for x, actual in zip(client_data[c], group_of[c]) if actual == g]
            if not X:
                continue
            indices = seed_indices(X, [Fraction(1)] * len(X), min(k, len(X)), tape(seed, "local", c, g))
            reps = [X[i] for i in indices]
            labels, _ = assignment(X, reps)
            counts = [labels.count(i) for i in range(len(reps))]
            snapped = [[float(round(rational(v) / rational(gamma)) * rational(gamma)) for v in row]
                       for row in reps] if gamma else [list(row) for row in reps]
            slices[f"{c}:{g}"] = {"selected_idx": indices, "mult": counts, "anchors": hex_centers(snapped)}
            anchors.extend(snapped)
            weights.extend(Fraction(count, sizes[g]) for count in counts)
    selected = seed_indices(anchors, weights, k, tape(seed, "server"))
    centers = [anchors[i][:] for i in selected]
    def weighted_cost(C):
        return sum(w * min(squared_distance(x, c) for c in C) for w, x in zip(weights, anchors))
    for _ in range(anchor_lloyd_iters):
        labels, _ = assignment(anchors, centers)
        proposed = []
        for j in range(k):
            mass = sum(w for w, label in zip(weights, labels) if label == j)
            if mass == 0:
                proposed.append(centers[j][:])
            else:
                proposed.append([float(sum(w * rational(x[h]) for w, x, label in zip(weights, anchors, labels)
                                           if label == j) / mass) for h in range(len(centers[j]))])
        if weighted_cost(proposed) <= weighted_cost(centers):
            centers = proposed
        else:
            break
    return centers, slices


def training(client_data, group_of, seed, k, T, L, bits, clip, gamma=0., anchor_lloyd_iters=0):
    integer_clients = {c: encode(x, bits, clip) for c, x in client_data.items()}
    represented = {c: [[float(Fraction(v, 2 ** bits)) for v in row] for row in x]
                   for c, x in integer_clients.items()}
    centers, slices = initialize(represented, group_of, seed, k, gamma, anchor_lloyd_iters)
    trajectory, aggregates, branches = [hex_centers(centers)], [], []
    X = [row for c in sorted(represented) for row in represented[c]]
    Xi = [row for c in sorted(integer_clients) for row in integer_clients[c]]
    groups = [g for c in sorted(group_of) for g in group_of[c]]
    sizes = [groups.count(0), groups.count(1)]
    for _ in range(T):
        labels, _ = assignment(X, centers)
        N, S, SS = stats(Xi, groups, labels, k)
        aggregates.append((N, S, SS))
        centers, info = fair_update(centers, N, S, SS, sizes, 2 ** bits, L)
        branches.append(info)
        trajectory.append(hex_centers(centers))
    return {"trajectory": trajectory, "per_round_stats": aggregates, "slices": slices,
            "oracle_branches": branches}
