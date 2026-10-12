"""One new test per TDD cycle."""
from hzbin.binning import binned_weighted_mean



def test_single_bin_equal_sigma_is_arithmetic_mean():
    res = binned_weighted_mean([0.2, 0.4, 0.6], [1.0, 2.0, 6.0],
                               [1.0, 1.0, 1.0], [0.0, 1.0])
    assert res.mean[0] == 3.0
