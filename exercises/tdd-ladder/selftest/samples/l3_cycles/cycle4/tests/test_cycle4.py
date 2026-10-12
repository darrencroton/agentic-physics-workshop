"""One new test per TDD cycle."""
from hzbin.binning import binned_weighted_mean



def test_two_bins_with_closed_last_edge():
    res = binned_weighted_mean([0.5, 1.0, 2.0], [1.0, 2.0, 4.0],
                               [1.0, 1.0, 1.0], [0.0, 1.0, 2.0])
    assert list(res.n) == [1, 2]
    assert list(res.mean) == [1.0, 3.0]
