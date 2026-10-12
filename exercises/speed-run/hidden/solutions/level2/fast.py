"""Level 2 solution: strict numpy cell list, exact (the calibration code)."""

import numpy as np

BLOCK = 2_000_000


def _bin_into(counts, s, edges):
    """Take s (sums of squares), apply sqrt in place and add binned counts."""
    r = np.sqrt(s, out=s)
    r = r[(r >= edges[0]) & (r < edges[-1])]
    k = np.searchsorted(edges, r, side="right") - 1
    k = k[(k >= 0) & (k < len(counts))]
    counts += np.bincount(k, minlength=len(counts))


def _sum_squares(xa, ya, za, xb, yb, zb):
    """Return s[i, j] = dx*dx + dy*dy + dz*dz with d = a[i] - b[j]."""
    s = np.subtract.outer(xa, xb)
    s *= s
    t = np.subtract.outer(ya, yb)
    t *= t
    s += t
    np.subtract.outer(za, zb, out=t)
    t *= t
    s += t
    return s


def count_pairs(pos, edges):
    """Count unique pairs per half-open separation bin (see reference.py)."""
    pos = np.ascontiguousarray(pos, dtype=np.float64)
    edges = np.ascontiguousarray(edges, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"pos has shape {pos.shape}; expected (N, 3)")
    nbins = len(edges) - 1
    counts = np.zeros(nbins, dtype=np.int64)
    if len(pos) < 2:
        return counts

    lo = pos.min(axis=0)
    span = float((pos.max(axis=0) - lo).max())
    rmax = float(edges[-1]) * (1.0 + 1e-9)
    nc = min(max(int(span // rmax), 1), 128)
    side = max(span / nc, rmax)
    idx = np.minimum(((pos - lo) // side).astype(np.int64), nc - 1)
    cell = (idx[:, 0] * nc + idx[:, 1]) * nc + idx[:, 2]
    order = np.argsort(cell, kind="stable")
    x, y, z = (np.ascontiguousarray(pos[order, d]) for d in range(3))
    start = np.searchsorted(cell[order], np.arange(nc**3 + 1))

    def run(cx, cy, z0, z1):
        """Index range of cells (cx, cy, z0..z1), clipped to the grid."""
        if not (0 <= cx < nc and 0 <= cy < nc):
            return 0, 0
        z0, z1 = max(z0, 0), min(z1, nc - 1)
        base = (cx * nc + cy) * nc
        return start[base + z0], start[base + z1 + 1]

    for cx in range(nc):
        for cy in range(nc):
            for cz in range(nc):
                a0, a1 = run(cx, cy, cz, cz)
                if a1 - a0 == 0:
                    continue
                runs = [
                    run(cx, cy, cz + 1, cz + 1),
                    run(cx, cy + 1, cz - 1, cz + 1),
                    run(cx + 1, cy - 1, cz - 1, cz + 1),
                    run(cx + 1, cy, cz - 1, cz + 1),
                    run(cx + 1, cy + 1, cz - 1, cz + 1),
                ]
                nb = np.concatenate([np.arange(b0, b1) for b0, b1 in runs])
                step = max(1, BLOCK // max(len(nb), a1 - a0, 1))
                for i0 in range(a0, a1, step):
                    i1 = min(i0 + step, a1)
                    xa, ya, za = x[i0:i1], y[i0:i1], z[i0:i1]
                    s = _sum_squares(xa, ya, za, x[i0:a1], y[i0:a1], z[i0:a1])
                    s = s[np.triu_indices(i1 - i0, 1, a1 - i0)]
                    _bin_into(counts, s, edges)
                    if len(nb):
                        s = _sum_squares(xa, ya, za, x[nb], y[nb], z[nb])
                        _bin_into(counts, s.ravel(), edges)
    return counts
