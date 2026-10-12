"""Quick tests written after the code, with expected values from a run."""
import numpy as np

from hzbin.binning import binned_weighted_mean

EDGES = [0, 1, 2, 3]


def test_basic_mean():
    res = binned_weighted_mean([0.5, 1.5, 2.5], [1, 2, 3], [1, 1, 1], EDGES)
    assert list(res.mean) == [1.0, 2.0, 3.0]


def test_x_eff_is_bin_centre():
    res = binned_weighted_mean([0.2, 1.3, 2.9], [1, 2, 3], [1, 1, 1], EDGES)
    assert np.allclose(res.x_eff, [0.5, 1.5, 2.5])


def test_error_of_two_points():
    res = binned_weighted_mean([0.2, 0.4], [1, 5], [1, 1], EDGES)
    assert np.isclose(res.err[0], 1.4142135623730951)
