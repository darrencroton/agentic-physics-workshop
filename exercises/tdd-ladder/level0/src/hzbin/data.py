"""Loading the mock H(z) measurements."""
import csv

import numpy as np


def load_hz(path="data/hz_mock.csv"):
    """Read H(z) measurements from a CSV file with columns z, H, sigma_H.

    Returns
    -------
    (z, H, sigma) : tuple of 1-D float64 numpy arrays
    """
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    z = np.array([float(r["z"]) for r in rows])
    h = np.array([float(r["H"]) for r in rows])
    sigma = np.array([float(r["sigma_H"]) for r in rows])
    return z, h, sigma
