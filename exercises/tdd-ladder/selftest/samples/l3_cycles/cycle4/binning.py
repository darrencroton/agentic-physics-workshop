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
    """Weighted mean and error per bin; last bin closed."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = 1.0 / np.asarray(sigma, dtype=float) ** 2
    edges = np.asarray(edges, dtype=float)
    n_bins = edges.size - 1
    idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, n_bins - 1)
    sw = np.bincount(idx, weights=w, minlength=n_bins)
    swy = np.bincount(idx, weights=w * y, minlength=n_bins)
    n = np.bincount(idx, minlength=n_bins)
    return BinnedResult(np.full(n_bins, np.nan), swy / sw, sw ** -0.5, n, 0)
