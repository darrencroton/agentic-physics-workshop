"""One new test per TDD cycle."""
from hzbin.binning import binned_weighted_mean



def test_out_of_range_points_are_dropped_and_counted():
    res = binned_weighted_mean([-1.0, 0.5, 1.5, 5.0], [9.0, 1.0, 3.0, 9.0],
                               [1.0, 1.0, 1.0, 1.0], [0.0, 1.0, 2.0])
    assert list(res.n) == [1, 1]
    assert list(res.mean) == [1.0, 3.0]
    assert res.n_dropped == 2
