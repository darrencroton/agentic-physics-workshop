"""Binning of measurements with uncertainties."""
from typing import NamedTuple

import numpy as np


class BinnedResult(NamedTuple):
    """Result of binning: one entry per bin, plus a count of dropped points.

    Attributes
    ----------
    x_eff : numpy.ndarray
        Effective x position of each bin.
    mean : numpy.ndarray
        Combined y value in each bin.
    err : numpy.ndarray
        Uncertainty on the combined y value in each bin.
    n : numpy.ndarray
        Number of points in each bin.
    n_dropped : int
        Number of input points that were not placed in any bin.
    """

    x_eff: np.ndarray
    mean: np.ndarray
    err: np.ndarray
    n: np.ndarray
    n_dropped: int


def binned_weighted_mean(x, y, sigma, edges) -> BinnedResult:
    """Bin measurements y(x) with uncertainties sigma and combine each bin.

    Parameters
    ----------
    x : array-like, shape (N,)
        Positions of the measurements (for example redshift).
    y : array-like, shape (N,)
        Measured values (for example H(z)).
    sigma : array-like, shape (N,)
        One-sigma uncertainty of each y value.
    edges : array-like, shape (K + 1,)
        Bin edges, defining K bins.

    Returns
    -------
    BinnedResult
        Named tuple (x_eff, mean, err, n, n_dropped); the first four fields
        are arrays with one entry per bin.
    """
    raise NotImplementedError("binned_weighted_mean is not implemented yet")
