"""Generate the mock cosmic-chronometer H(z) data set (level0/data/hz_mock.csv).

Flat LCDM with H0 = 70 and Omega_m = 0.3, heteroscedastic Gaussian noise.
Run with a Python that has numpy: python make_data.py
"""
from pathlib import Path

import numpy as np

SEED = 20240611
H0, OM = 70.0, 0.3
EDGE_POINTS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.75, 2.0]
N_RANDOM = 33
OUT = Path(__file__).parent / "level0" / "data" / "hz_mock.csv"


def hubble(z):
    """Flat LCDM Hubble rate in km/s/Mpc."""
    return H0 * np.sqrt(OM * (1.0 + z) ** 3 + 1.0 - OM)


def main():
    """Write the CSV with columns z, H, sigma_H."""
    rng = np.random.default_rng(SEED)
    z = []
    while len(z) < N_RANDOM:
        c = round(float(rng.uniform(0.07, 2.0)), 3)
        if 1.5 <= c < 1.75 or c in EDGE_POINTS or c in z:
            continue
        z.append(c)
    z = np.sort(np.array(z + EDGE_POINTS))
    z = np.array([float(f"{v:.6g}") for v in z])
    h_true = hubble(z)
    frac = rng.uniform(0.04, 0.20, size=z.size)
    sigma = np.array([float(f"{v:.6g}") for v in frac * h_true])
    h = np.array([float(f"{v:.6g}") for v in h_true + rng.normal(0, sigma)])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write("z,H,sigma_H\n")
        for row in zip(z, h, sigma):
            fh.write(",".join(f"{v:.6g}" for v in row) + "\n")
    print(f"wrote {z.size} rows to {OUT}")


if __name__ == "__main__":
    main()
