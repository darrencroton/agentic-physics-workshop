"""Race entry: starts as a copy of the reference pair counter; make it fast.

count_pairs(pos, edges) counts every unique pair i < j once. For each pair:

    d = pos[i] - pos[j]
    r = math.sqrt(dx*dx + dy*dy + dz*dz)      (float64, in this order)

and the pair goes in bin k when edges[k] <= r < edges[k+1] (half-open bins).
Pairs with r < edges[0] or r >= edges[-1] are not counted. The box is not
periodic. The result is an int64 array of length len(edges) - 1.
"""

import bisect
import math

import numpy as np


def count_pairs(pos, edges):
    """Count unique pairs per separation bin with a pure-Python double loop."""
    rows = np.asarray(pos, dtype=np.float64).tolist()
    edges = [float(e) for e in edges]
    nbins = len(edges) - 1
    counts = [0] * nbins
    n = len(rows)
    for i in range(n):
        xi, yi, zi = rows[i]
        for j in range(i + 1, n):
            xj, yj, zj = rows[j]
            dx = xi - xj
            dy = yi - yj
            dz = zi - zj
            r = math.sqrt(dx * dx + dy * dy + dz * dz)
            k = bisect.bisect_right(edges, r) - 1
            if 0 <= k < nbins:
                counts[k] += 1
    return np.array(counts, dtype=np.int64)
