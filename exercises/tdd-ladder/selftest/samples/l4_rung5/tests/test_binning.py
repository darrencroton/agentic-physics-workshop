"""Rung-5 suite: spec-driven examples plus property tests."""
import math

import numpy as np
import pytest

from hzbin.binning import binned_weighted_mean

EDGES = [0.0, 1.0, 2.0, 3.0]


# ---- Worked examples with hand-computed oracles ----

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


def test_points_outside_are_excluded_and_counted_on_both_sides():
    res = binned_weighted_mean([-0.5, 0.5, 3.5, 9.0], [100.0, 1.0, 100.0, 7.0],
                               [1.0] * 4, EDGES)
    assert list(res.n) == [1, 0, 0]
    assert res.mean[0] == 1.0
    assert res.n_dropped == 3


def test_weighted_mean_uses_inverse_variance():
    res = binned_weighted_mean([0.5, 0.5], [1.0, 4.0], [1.0, 2.0], EDGES)
    assert res.mean[0] == pytest.approx(1.6)


def test_error_with_unequal_sigma():
    res = binned_weighted_mean([0.2, 0.4], [1.0, 1.0], [3.0, 4.0], EDGES)
    assert res.err[0] == pytest.approx(2.4)


def test_x_eff_is_weighted_position():
    res = binned_weighted_mean([0.2, 0.8], [1.0, 1.0], [1.0, 2.0], EDGES)
    assert res.x_eff[0] == pytest.approx(0.32)


def test_empty_bin_gives_nan_and_zero_count():
    res = binned_weighted_mean([0.5, 2.5], [1.0, 2.0], [1.0, 1.0], EDGES)
    assert res.n[1] == 0
    assert math.isnan(res.mean[1]) and math.isnan(res.err[1])
    assert math.isnan(res.x_eff[1])


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_values_raise(bad):
    with pytest.raises(ValueError):
        binned_weighted_mean([0.5, 1.5], [1.0, bad], [1.0, 1.0], EDGES)
    with pytest.raises(ValueError):
        binned_weighted_mean([bad, 1.5], [1.0, 1.0], [1.0, 1.0], EDGES)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_non_positive_sigma_raises(bad):
    with pytest.raises(ValueError):
        binned_weighted_mean([0.5, 1.5], [1.0, 2.0], [1.0, bad], EDGES)


@pytest.mark.parametrize("edges", [[3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 1.0],
                                   [0.0]])
def test_bad_edges_raise(edges):
    with pytest.raises(ValueError):
        binned_weighted_mean([0.5], [1.0], [1.0], edges)


def test_inputs_are_not_modified():
    x = np.array([2.5, 0.5, 1.5])
    y = np.array([3.0, 1.0, 2.0])
    s = np.array([1.0, 2.0, 1.0])
    before = (x.copy(), y.copy(), s.copy())
    binned_weighted_mean(x, y, s, EDGES)
    for now, then in zip((x, y, s), before):
        assert np.array_equal(now, then)


# ---- Property tests ----

def _random_data(rng, n=200):
    x = rng.uniform(-0.5, 3.5, n)
    y = rng.normal(10.0, 3.0, n)
    s = rng.uniform(0.5, 2.0, n)
    return x, y, s


def test_permutation_invariance():
    rng = np.random.default_rng(1)
    x, y, s = _random_data(rng)
    p = rng.permutation(x.size)
    a = binned_weighted_mean(x, y, s, EDGES)
    b = binned_weighted_mean(x[p], y[p], s[p], EDGES)
    for fa, fb in zip(a[:3], b[:3]):
        np.testing.assert_allclose(fa, fb, rtol=1e-12)
    assert np.array_equal(a.n, b.n) and a.n_dropped == b.n_dropped


def test_uniform_sigma_gives_arithmetic_mean_and_sigma_over_root_n():
    rng = np.random.default_rng(2)
    x = rng.uniform(0.0, 3.0, 90)
    y = rng.normal(0.0, 1.0, 90)
    res = binned_weighted_mean(x, y, np.full(90, 0.7), EDGES)
    for k in range(3):
        sel = (x >= k) & (x < k + 1)
        assert res.mean[k] == pytest.approx(y[sel].mean(), rel=1e-12)
        assert res.err[k] == pytest.approx(0.7 / np.sqrt(sel.sum()),
                                           rel=1e-12)


def test_affine_equivariance():
    rng = np.random.default_rng(3)
    x, y, s = _random_data(rng)
    a, b = -2.5, 40.0
    base = binned_weighted_mean(x, y, s, EDGES)
    moved = binned_weighted_mean(x, a * y + b, abs(a) * s, EDGES)
    np.testing.assert_allclose(moved.mean, a * base.mean + b, rtol=1e-12)
    np.testing.assert_allclose(moved.err, abs(a) * base.err, rtol=1e-12)


def test_bin_merging_matches_coarser_binning():
    rng = np.random.default_rng(4)
    x, y, s = _random_data(rng)
    fine = binned_weighted_mean(x, y, s, [0.0, 1.0, 2.0, 3.0])
    coarse = binned_weighted_mean(x, y, s, [0.0, 2.0, 3.0])
    w = 1.0 / fine.err[:2] ** 2
    assert coarse.mean[0] == pytest.approx(np.sum(w * fine.mean[:2]) / w.sum(),
                                           rel=1e-12)
    assert coarse.err[0] == pytest.approx(w.sum() ** -0.5, rel=1e-12)
    assert coarse.x_eff[0] == pytest.approx(
        np.sum(w * fine.x_eff[:2]) / w.sum(), rel=1e-12)
    assert coarse.n[0] == fine.n[:2].sum()


def test_coverage_of_one_sigma_error():
    rng = np.random.default_rng(12345)
    n_bins, per_bin, reps, mu = 50, 4, 50, 3.0
    edges = np.arange(n_bins + 1, dtype=float)
    hits = 0
    for _ in range(reps):
        x = np.repeat(np.arange(n_bins) + 0.5, per_bin)
        s = rng.uniform(0.5, 3.0, x.size)
        y = rng.normal(mu, s)
        res = binned_weighted_mean(x, y, s, edges)
        hits += np.count_nonzero(np.abs(res.mean - mu) < res.err)
    frac = hits / (n_bins * reps)
    sd = math.sqrt(0.6827 * (1 - 0.6827) / (n_bins * reps))
    assert abs(frac - 0.6827) < 4 * sd


def test_float32_input_matches_float64_computation():
    k = np.arange(1600)
    y32 = (1.0e6 + (k % 16) * 0.0625 + 0.001 * (k % 7)).astype(np.float32)
    x32 = np.full(1600, 0.5, dtype=np.float32)
    s32 = np.full(1600, 2.0, dtype=np.float32)
    got = binned_weighted_mean(x32, y32, s32, EDGES)
    want = binned_weighted_mean(x32.astype(np.float64),
                                y32.astype(np.float64),
                                s32.astype(np.float64), EDGES)
    assert got.mean[0] == pytest.approx(want.mean[0], rel=1e-12)
    assert got.err[0] == pytest.approx(want.err[0], rel=1e-12)
