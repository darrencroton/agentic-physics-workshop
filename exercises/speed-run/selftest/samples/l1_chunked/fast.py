"""Race entry: chunked numpy brute force, exact and memory-bounded (Level 1).

Same contract as reference.py. Rows are processed in blocks of CHUNK; each
block is compared with itself and every later point, so only a CHUNK x N
slab of float64 is alive at once (two slabs: about 160 MB at N = 20000)
instead of an N x N matrix (3.2 GB per temporary at N = 20000).
"""

import numpy as np

CHUNK = 500


def count_pairs(pos, edges):
    """Count unique pairs per half-open separation bin (see reference.py)."""
    pos = np.ascontiguousarray(pos, dtype=np.float64)
    edges = np.ascontiguousarray(edges, dtype=np.float64)
    nbins = len(edges) - 1
    counts = np.zeros(nbins, dtype=np.int64)
    x, y, z = (np.ascontiguousarray(pos[:, d]) for d in range(3))
    n = len(pos)
    for i0 in range(0, n, CHUNK):
        i1 = min(i0 + CHUNK, n)
        s = np.subtract.outer(x[i0:i1], x[i0:])
        s *= s
        t = np.subtract.outer(y[i0:i1], y[i0:])
        t *= t
        s += t
        np.subtract.outer(z[i0:i1], z[i0:], out=t)
        t *= t
        s += t
        s[np.tril_indices(i1 - i0)] = np.inf
        r = np.sqrt(s, out=s)
        r = r[(r >= edges[0]) & (r < edges[-1])]
        k = np.searchsorted(edges, r, side="right") - 1
        counts += np.bincount(k[(k >= 0) & (k < nbins)], minlength=nbins)
    return counts
