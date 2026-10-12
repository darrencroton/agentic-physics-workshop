"""One new test per TDD cycle."""
from hzbin.binning import binned_weighted_mean



def test_error_is_inverse_sqrt_of_summed_weights():
    res = binned_weighted_mean([0.1, 0.2, 0.3, 0.4], [1.0, 2.0, 3.0, 4.0],
                               [1.0, 1.0, 1.0, 1.0], [0.0, 1.0])
    assert abs(res.err[0] - 0.5) < 1e-12
