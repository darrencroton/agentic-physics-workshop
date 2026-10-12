"""Sample entry: the whole N x N distance matrix in one go (Level 1 trap).

Correct, but every line below makes at least one N x N float64 temporary
(3.2 GB each at N = 20000), so the harness kills it at the 2.5 GB cap.
"""

import numpy as np


def count_pairs(pos, edges):
    """Count unique pairs per half-open separation bin (see reference.py)."""
    pos = np.asarray(pos, dtype=np.float64)
    edges = np.asarray(edges, dtype=np.float64)
    dx = pos[:, 0][:, None] - pos[:, 0][None, :]
    dy = pos[:, 1][:, None] - pos[:, 1][None, :]
    dz = pos[:, 2][:, None] - pos[:, 2][None, :]
    r = np.sqrt(dx * dx + dy * dy + dz * dz)
    r = r[np.triu_indices(len(pos), 1)]
    k = np.searchsorted(edges, r, side="right") - 1
    k = k[(k >= 0) & (k < len(edges) - 1)]
    return np.bincount(k, minlength=len(edges) - 1).astype(np.int64)
