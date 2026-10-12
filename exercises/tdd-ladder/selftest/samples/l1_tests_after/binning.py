"""Sample implementation used by the exercise self-test."""
from typing import NamedTuple

import numpy as np


class BinnedResult(NamedTuple):
    """Result of binning."""

    x_eff: np.ndarray
    mean: np.ndarray
    err: np.ndarray
    n: np.ndarray
    n_dropped: int



def binned_weighted_mean(x, y, sigma, edges):
    """Bin y(x) and return inverse-variance weighted means."""
    x = np.asarray(x)
    y = np.asarray(y)
    sigma = np.asarray(sigma)
    if not (len(x) == len(y) == len(sigma)):
        raise ValueError("x, y and sigma must have the same length")
    if np.any(sigma <= 0):
        raise ValueError("sigma must be positive")
    n_bins = len(edges) - 1
    x_eff = np.full(n_bins, np.nan)
    mean = np.full(n_bins, np.nan)
    err = np.full(n_bins, np.nan)
    n = np.zeros(n_bins, dtype=int)
    n_dropped = 0
    for i in range(n_bins):
        m = (x >= edges[i]) & (x < edges[i + 1])
        n[i] = m.sum()
        if n[i] == 0:
            continue
        w = 1 / sigma[m] ** 2
        x_eff[i] = np.sum(w * x[m]) / np.sum(w)
        mean[i] = np.sum(w * y[m]) / np.sum(w)
        err[i] = np.sum(w) ** -0.5
    n_dropped = len(x) - n.sum()
    return BinnedResult(x_eff, mean, err, n, n_dropped)
