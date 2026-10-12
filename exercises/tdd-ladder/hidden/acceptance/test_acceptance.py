"""Client acceptance tests for binned_weighted_mean (CLIENT_SPEC S1-S10)."""
import math

import numpy as np
import pytest

from hzbin.binning import BinnedResult, binned_weighted_mean

EDGES = [0.0, 1.0, 2.0, 3.0]


def test_s1_bin_edge_convention():
    """Interior bins are [e_k, e_k+1); the last bin also includes its edge."""
    res = binned_weighted_mean([0.0, 1.0, 2.0, 3.0], [1, 1, 1, 1],
                               [1, 1, 1, 1], EDGES)
    assert list(res.n) == [1, 1, 2]
    assert res.n_dropped == 0


def test_s2_out_of_range_points_dropped_and_counted():
    """Points below e0 or above en are excluded and counted."""
    res = binned_weighted_mean([-1.0, 0.5, 1.5, 3.5, 4.0], [1, 1, 1, 1, 1],
                               [1, 1, 1, 1, 1], EDGES)
    assert list(res.n) == [1, 1, 0]
    assert res.n_dropped == 3
    assert isinstance(res.n_dropped, (int, np.integer))


def test_s3_inverse_variance_weights():
    """y = 1, 4 with sigma = 1, 2 gives weights 1, 1/4 and mean 8/5."""
    res = binned_weighted_mean([0.5, 0.5], [1.0, 4.0], [1.0, 2.0], EDGES)
    assert res.mean[0] == pytest.approx(1.6, rel=1e-12)


def test_s4_error_is_uncertainty_of_weighted_mean():
    """Four points with sigma = 1 give err = 4**-0.5 = 0.5, not the scatter."""
    res = binned_weighted_mean([0.1, 0.2, 0.3, 0.4], [1.0, 2.0, 3.0, 4.0],
                               [1.0, 1.0, 1.0, 1.0], EDGES)
    assert res.mean[0] == pytest.approx(2.5, rel=1e-12)
    assert res.err[0] == pytest.approx(0.5, rel=1e-12)


def test_s5_x_eff_is_weighted_mean_position():
    """x = 0.2, 0.8 with weights 1, 1/4 gives x_eff = 0.4 / 1.25 = 0.32."""
    res = binned_weighted_mean([0.2, 0.8], [1.0, 1.0], [1.0, 2.0], EDGES)
    assert res.x_eff[0] == pytest.approx(0.32, rel=1e-12)


def test_s6_empty_bin_is_nan_with_zero_count():
    """The middle bin is empty: NaN x_eff, mean, err and n = 0."""
    res = binned_weighted_mean([0.5, 2.5], [1.0, 2.0], [1.0, 1.0], EDGES)
    assert res.n[1] == 0
    assert math.isnan(res.x_eff[1])
    assert math.isnan(res.mean[1])
    assert math.isnan(res.err[1])
    assert res.mean[0] == 1.0 and res.mean[2] == 2.0


def test_s7_non_finite_input_raises():
    """NaN or inf in x, y or sigma raises ValueError."""
    good = {"x": [0.5, 1.5], "y": [1.0, 2.0], "sigma": [1.0, 1.0]}
    for key in good:
        for bad in (float("nan"), float("inf"), float("-inf")):
            args = {k: list(v) for k, v in good.items()}
            args[key][1] = bad
            with pytest.raises(ValueError):
                binned_weighted_mean(args["x"], args["y"], args["sigma"],
                                     EDGES)


def test_s8_non_positive_sigma_raises():
    """sigma = 0 or sigma < 0 raises ValueError."""
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError):
            binned_weighted_mean([0.5, 1.5], [1.0, 2.0], [1.0, bad], EDGES)


def test_s9_invalid_edges_and_shapes_raise():
    """Bad edges, mismatched lengths and non-1-D inputs raise ValueError."""
    x, y, s = [0.5, 1.5], [1.0, 2.0], [1.0, 1.0]
    bad_edges = ([0.0], [], [3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 1.0, 2.0],
                 [0.0, 2.0, 1.0, 3.0])
    for edges in bad_edges:
        with pytest.raises(ValueError):
            binned_weighted_mean(x, y, s, edges)
    with pytest.raises(ValueError):
        binned_weighted_mean(x, [1.0], s, EDGES)
    with pytest.raises(ValueError):
        binned_weighted_mean(x, y, [1.0, 1.0, 1.0], EDGES)
    with pytest.raises(ValueError):
        binned_weighted_mean([[0.5, 1.5]], [[1.0, 2.0]], [[1.0, 1.0]], EDGES)


def test_s10_inputs_not_modified():
    """Unsorted input arrays and edges are left exactly as given."""
    x = np.array([2.5, 0.5, 1.5, 0.7])
    y = np.array([3.0, 1.0, 2.0, 1.5])
    s = np.array([1.0, 2.0, 1.0, 0.5])
    edges = np.array(EDGES)
    copies = [a.copy() for a in (x, y, s, edges)]
    binned_weighted_mean(x, y, s, edges)
    for original, copy in zip((x, y, s, edges), copies):
        assert np.array_equal(original, copy)


def test_s10_lists_accepted_and_output_types():
    """Lists work; outputs are float64 arrays, n int64, n_dropped int."""
    res = binned_weighted_mean([0.5, 1.5, 9.0], [1, 2, 3], [1, 1, 1], EDGES)
    assert isinstance(res, BinnedResult)
    assert res._fields == ("x_eff", "mean", "err", "n", "n_dropped")
    for field in (res.x_eff, res.mean, res.err):
        assert isinstance(field, np.ndarray) and field.dtype == np.float64
        assert field.shape == (3,)
    assert isinstance(res.n, np.ndarray) and np.issubdtype(res.n.dtype, np.integer)
    assert isinstance(res.n_dropped, (int, np.integer)) and res.n_dropped == 1


def test_s10_float32_input_accumulated_in_float64():
    """1600 float32 values near 1e6 average to exactly 1000000.46875."""
    k = np.arange(1600)
    y = (1.0e6 + (k % 16) * 0.0625).astype(np.float32)
    x = np.full(1600, 0.5, dtype=np.float32)
    s = np.ones(1600, dtype=np.float32)
    res = binned_weighted_mean(x, y, s, EDGES)
    assert res.mean.dtype == np.float64
    assert res.mean[0] == pytest.approx(1000000.46875, abs=1e-6)
    assert res.err[0] == pytest.approx(0.025, rel=1e-12)
