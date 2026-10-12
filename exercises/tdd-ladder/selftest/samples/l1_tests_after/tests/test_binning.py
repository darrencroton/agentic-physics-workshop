"""Tests written from reading the code: they restate its formulas."""
import numpy as np
import pytest

from hzbin.binning import binned_weighted_mean

EDGES = [0.0, 1.0]
X = np.array([0.2, 0.5, 0.9])
Y = np.array([1.0, 2.0, 4.0])
S = np.array([1.0, 2.0, 0.5])


def test_weighted_mean_formula():
    w = 1 / S**2
    res = binned_weighted_mean(X, Y, S, EDGES)
    assert res.mean[0] == pytest.approx(np.sum(w * Y) / np.sum(w))


def test_error_formula():
    w = 1 / S**2
    res = binned_weighted_mean(X, Y, S, EDGES)
    assert res.err[0] == pytest.approx(np.sum(w) ** -0.5)


def test_x_eff_formula():
    w = 1 / S**2
    res = binned_weighted_mean(X, Y, S, EDGES)
    assert res.x_eff[0] == pytest.approx(np.sum(w * X) / np.sum(w))


def test_empty_bin_is_nan():
    res = binned_weighted_mean(X, Y, S, [0.0, 1.0, 2.0])
    assert np.isnan(res.mean[1])
    assert res.n[1] == 0


def test_zero_sigma_raises():
    with pytest.raises(ValueError):
        binned_weighted_mean(X, Y, [1.0, 0.0, 1.0], EDGES)

