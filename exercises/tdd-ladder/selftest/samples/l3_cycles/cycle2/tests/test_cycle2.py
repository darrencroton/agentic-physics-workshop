"""One new test per TDD cycle."""
from hzbin.binning import binned_weighted_mean



def test_unequal_sigma_gives_inverse_variance_mean():
    res = binned_weighted_mean([0.2, 0.4], [1.0, 4.0], [1.0, 2.0],
                               [0.0, 1.0])
    assert abs(res.mean[0] - 1.6) < 1e-12
