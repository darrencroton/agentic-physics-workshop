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
    """Arithmetic mean of y in a single bin."""
    y = np.asarray(y, dtype=float)
    return BinnedResult(np.array([np.nan]), np.array([y.mean()]),
                        np.array([np.nan]), np.array([y.size]), 0)
