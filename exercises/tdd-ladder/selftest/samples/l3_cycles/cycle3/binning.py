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
    """Weighted mean and its error for a single bin."""
    y = np.asarray(y, dtype=float)
    w = 1.0 / np.asarray(sigma, dtype=float) ** 2
    return BinnedResult(np.array([np.nan]), np.array([np.sum(w * y) / w.sum()]),
                        np.array([w.sum() ** -0.5]), np.array([y.size]), 0)
