"""Per-round digests for the exactness check.

The specification's equality test is "hashes of indexed centers, exact
(N,S,SS), and final model bytes must match." Recording one digest per round
as training/replay proceeds turns that into a digest comparison instead of
a bespoke harness, and pinpoints which round first diverged for free.
"""
import hashlib


def round_digest(centers, N, S, SS) -> str:
    h = hashlib.sha256()
    h.update(centers.tobytes())
    h.update(repr(N).encode("utf-8"))
    h.update(repr(S).encode("utf-8"))
    h.update(repr(SS).encode("utf-8"))
    return h.hexdigest()
