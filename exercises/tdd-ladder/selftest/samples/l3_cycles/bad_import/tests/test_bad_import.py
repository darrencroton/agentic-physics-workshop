"""A test that cannot even be collected: it imports a name that is missing."""
from hzbin.binning import weighted_bin_mean


def test_uses_missing_name():
    assert weighted_bin_mean([0.5], [1.0], [1.0], [0.0, 1.0])
