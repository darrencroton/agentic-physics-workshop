"""Pair counting in a 100 Mpc/h box: shared constants and the catalogue loader.

BOX is the box side in Mpc/h. EDGES are the 16 separation bin edges in Mpc/h
(15 logarithmic bins from 0.5 to 10). They are fixed literals so every
implementation bins against exactly the same float64 values.
"""

from pathlib import Path

import numpy as np

BOX = 100.0

EDGES = (
    0.5,
    0.6105276500337841,
    0.7454880229115495,
    0.9102821015130402,
    1.111504784609142,
    1.3572088082974534,
    1.6572270086699938,
    2.0235658223516175,
    2.4708857724180295,
    3.017088168272582,
    3.6840314986403864,
    4.498406187030711,
    5.492802716530591,
    6.707015869245212,
    8.189637274779155,
    10.0,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATALOGUES = ("mock_2k", "mock_20k", "mock_200k")


def load_catalogue(name_or_path):
    """Return a catalogue as an (N, 3) C-ordered float64 array.

    name_or_path is "mock_2k", "mock_20k", "mock_200k" or a .npy file path.
    """
    name = str(name_or_path)
    path = DATA_DIR / f"{name}.npy" if name in CATALOGUES else Path(name)
    if not path.is_file():
        raise FileNotFoundError(f"no catalogue at {path}")
    pos = np.load(path, allow_pickle=False)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"{path} has shape {pos.shape}; expected (N, 3)")
    return np.ascontiguousarray(pos, dtype=np.float64)
