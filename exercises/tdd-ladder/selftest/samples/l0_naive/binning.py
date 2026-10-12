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
    """Bin y(x) and return a weighted mean per bin."""
    x = np.asarray(x)
    y = np.asarray(y)
    sigma = np.asarray(sigma)
    n_bins = len(edges) - 1
    x_eff, mean, err, n = [], [], [], []
    for i in range(n_bins):
        m = (x >= edges[i]) & (x < edges[i + 1])
        n.append(int(m.sum()))
        if m.sum() == 0:
            x_eff.append(0.0)
            mean.append(0.0)
            err.append(0.0)
            continue
        w = 1 / sigma[m] ** 2
        x_eff.append((edges[i] + edges[i + 1]) / 2)
        mean.append(np.sum(w * y[m]) / np.sum(w))
        err.append(np.std(y[m]) / np.sqrt(m.sum()))
    n_dropped = len(x) - sum(n)
    return BinnedResult(np.array(x_eff), np.array(mean), np.array(err),
                        np.array(n), n_dropped)
