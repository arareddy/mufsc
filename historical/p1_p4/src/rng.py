"""Versioned deterministic PRNG execution; ideal-bit theorem is separate."""
import numpy as np
_ROLE_IDS={'local':1,'server':2,'merged_local':3,'merged_server':4,'centralized':5}


def canonical_tape(seed,role,*entity_ids):
    if role not in _ROLE_IDS:raise ValueError('unknown tape role')
    ids=(seed,*entity_ids)
    if any(isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,np.integer)) or x<0 for x in ids):
        raise ValueError('tape IDs must be nonnegative integers')
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed),_ROLE_IDS[role],*[int(x) for x in entity_ids]])))


def random_below(total,rng):
    """Unbiased under iid fair raw bits. Discard unused bits on every trial."""
    if not isinstance(total,int) or total<1:raise ValueError('positive integer total required')
    bits=(total-1).bit_length()
    if bits==0:return 0
    words=(bits+63)//64;mask=(1<<bits)-1
    while True:
        value=0
        for word in range(words):value |= int(rng.bit_generator.random_raw())<<(64*word)
        value &= mask
        if value<total:return value
