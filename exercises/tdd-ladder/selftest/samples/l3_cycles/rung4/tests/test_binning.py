"""Rung-4 suite: spec-driven tests with hand-computed expected values."""
import math

import pytest

from hzbin.binning import binned_weighted_mean

EDGES = [0.0, 1.0, 2.0, 3.0]
ONES = [1.0, 1.0, 1.0, 1.0]


def test_interior_edge_belongs_to_upper_bin():
    res = binned_weighted_mean([1.0], [5.0], [1.0], EDGES)
    assert list(res.n) == [0, 1, 0]


def test_first_edge_is_included():
    res = binned_weighted_mean([0.0], [5.0], [1.0], EDGES)
    assert list(res.n) == [1, 0, 0]


def test_last_edge_is_included_in_last_bin():
    res = binned_weighted_mean([3.0], [5.0], [1.0], EDGES)
    assert list(res.n) == [0, 0, 1]
    assert res.mean[2] == 5.0


def test_points_outside_are_excluded():
    res = binned_weighted_mean([-0.5, 0.5, 3.5], [100.0, 1.0, 100.0],
                               [1.0, 1.0, 1.0], EDGES)
    assert list(res.n) == [1, 0, 0]
    assert res.mean[0] == 1.0


def test_points_below_first_edge_are_counted_as_dropped():
    res = binned_weighted_mean([-0.5, -2.0, 0.5], [1.0, 1.0, 1.0],
                               [1.0, 1.0, 1.0], EDGES)
    assert res.n_dropped == 2


def test_weighted_mean_uses_inverse_variance():
    res = binned_weighted_mean([0.5, 0.5], [1.0, 4.0], [1.0, 2.0], EDGES)
    assert res.mean[0] == pytest.approx(1.6)


def test_error_is_uncertainty_of_the_mean():
    res = binned_weighted_mean([0.1, 0.2, 0.3, 0.4], [1.0, 2.0, 3.0, 4.0],
                               ONES, EDGES)
    assert res.err[0] == pytest.approx(0.5)


def test_error_with_unequal_sigma():
    res = binned_weighted_mean([0.2, 0.4], [1.0, 1.0], [3.0, 4.0], EDGES)
    assert res.err[0] == pytest.approx(2.4)


def test_x_eff_is_weighted_position():
    res = binned_weighted_mean([0.2, 0.8], [1.0, 1.0], [1.0, 2.0], EDGES)
    assert res.x_eff[0] == pytest.approx(0.32)


def test_empty_bin_gives_nan_and_zero_count():
    res = binned_weighted_mean([0.5, 2.5], [1.0, 2.0], [1.0, 1.0], EDGES)
    assert res.n[1] == 0
    assert math.isnan(res.mean[1])
    assert math.isnan(res.err[1])
    assert math.isnan(res.x_eff[1])


def test_zero_sigma_raises():
    with pytest.raises(ValueError):
        binned_weighted_mean([0.5, 1.5], [1.0, 2.0], [1.0, 0.0], EDGES)
