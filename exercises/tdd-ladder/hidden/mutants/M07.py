"""Reference implementation of binned weighted means (CLIENT_SPEC S1-S10)."""
from typing import NamedTuple

import numpy as np


class BinnedResult(NamedTuple):
    """Result of binning: one entry per bin, plus a count of dropped points."""

    x_eff: np.ndarray
    mean: np.ndarray
    err: np.ndarray
    n: np.ndarray
    n_dropped: int


def _as_float_array(values, name):
    """Return a float64 copy of values, or raise ValueError."""
    try:
        return np.array(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric: {exc}") from exc


def binned_weighted_mean(x, y, sigma, edges) -> BinnedResult:
    """Bin measurements y(x) with uncertainties sigma and combine each bin.

    Bins are half-open [e_k, e_k+1) except the last, which is closed.
    Points outside [edges[0], edges[-1]] are excluded and counted in
    n_dropped. Each bin holds the inverse-variance weighted mean, its
    uncertainty (sum of weights)**-0.5, and the weighted mean position.
    Empty bins give NaN for x_eff, mean and err, and n = 0.

    Parameters
    ----------
    x, y, sigma : array-like, shape (N,)
        Positions, values and one-sigma uncertainties.
    edges : array-like, shape (K + 1,)
        Strictly increasing bin edges.

    Returns
    -------
    BinnedResult
        (x_eff, mean, err, n, n_dropped).

    Raises
    ------
    ValueError
        For bad shapes, non-finite inputs, sigma <= 0 or invalid edges.
    """
    x = _as_float_array(x, "x")
    y = _as_float_array(y, "y")
    sigma = _as_float_array(sigma, "sigma")
    edges = _as_float_array(edges, "edges")

    for name, arr in (("x", x), ("y", y), ("sigma", sigma)):
        if arr.ndim != 1:
            raise ValueError(f"{name} must be 1-D, got {arr.ndim}-D")
    if not (x.size == y.size == sigma.size):
        raise ValueError(
            f"x, y and sigma must have equal length, got "
            f"{x.size}, {y.size}, {sigma.size}")
    if edges.ndim != 1:
        raise ValueError(f"edges must be 1-D, got {edges.ndim}-D")

    for name, arr in (("x", x), ("y", y), ("sigma", sigma)):
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} contains non-finite values")

    if np.any(sigma <= 0):
        raise ValueError("sigma must be strictly positive")

    if edges.size < 2:
        raise ValueError("edges must have at least 2 elements")
    if not np.all(np.isfinite(edges)) or not np.all(np.diff(edges) > 0):
        raise ValueError("edges must be finite and strictly increasing")

    n_bins = edges.size - 1
    inside = (x >= edges[0]) & (x <= edges[-1])
    n_dropped = int(x.size - np.count_nonzero(inside))

    xi, yi, si = x[inside], y[inside], sigma[inside]
    idx = np.searchsorted(edges, xi, side="right") - 1
    idx = np.minimum(idx, n_bins - 1)

    w = 1.0 / si**2
    sw = np.bincount(idx, weights=w, minlength=n_bins)
    swy = np.bincount(idx, weights=w * yi, minlength=n_bins)
    swx = np.bincount(idx, weights=w * xi, minlength=n_bins)
    n = np.bincount(idx, minlength=n_bins).astype(np.int64)

    nonempty = n > 0
    x_eff = np.full(n_bins, np.nan)
    mean = np.full(n_bins, np.nan)
    err = np.full(n_bins, np.nan)
    x_eff[nonempty] = swx[nonempty] / sw[nonempty]
    mean[nonempty] = swy[nonempty] / sw[nonempty]
    for k in np.flatnonzero(nonempty):
        err[k] = np.std(yi[idx == k]) / np.sqrt(n[k])
    return BinnedResult(x_eff, mean, err, n, n_dropped)
