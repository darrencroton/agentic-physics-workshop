"""Race entry: cell-list pair counter in C (pairs.c), loaded with ctypes.

On first import pairs.c is compiled next to this file with
clang -O2 -ffp-contract=off -shared -fPIC -o _pairs_<hash>.so pairs.c
(skipped when that file exists; <hash> covers the flags and the source text, so
changing either rebuilds). -ffp-contract=off stops clang
fusing dx*dx + dy*dy + dz*dz into FMA, which would move a few pairs that sit
within an ulp of a bin edge. Same contract as reference.py.
"""

import ctypes
import hashlib
import shutil
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pairs.c"
FLAGS = ["-O2", "-ffp-contract=off", "-shared", "-fPIC"]


def _library():
    """Path of the library named by a hash of the flags and pairs.c."""
    digest = hashlib.sha256()
    digest.update(" ".join(FLAGS).encode())
    digest.update(SOURCE.read_bytes())
    return HERE / ("_pairs_%s.so" % digest.hexdigest()[:10])


LIBRARY = _library()


def _build():
    """Compile pairs.c to LIBRARY unless it exists; remove older builds."""
    if LIBRARY.exists():
        return
    for old in HERE.glob("_pairs_*.so"):
        old.unlink(missing_ok=True)
    clang = shutil.which("clang")
    if clang is None:
        raise RuntimeError(
            "clang not found: install the Xcode command line tools"
        )
    cmd = [clang, *FLAGS, "-o", str(LIBRARY), str(SOURCE)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"compiling pairs.c failed:\n{result.stderr}")


def _load():
    """Load the library and declare the count() signature."""
    _build()
    lib = ctypes.CDLL(str(LIBRARY))
    dbl = ctypes.POINTER(ctypes.c_double)
    lib.count.argtypes = [
        dbl,
        ctypes.c_longlong,
        dbl,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_longlong),
    ]
    lib.count.restype = None
    return lib


_LIB = _load()


def count_pairs(pos, edges):
    """Count unique pairs per half-open separation bin (see reference.py)."""
    pos = np.ascontiguousarray(pos, dtype=np.float64)
    edges = np.ascontiguousarray(edges, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"pos has shape {pos.shape}; expected (N, 3)")
    nbins = len(edges) - 1
    out = np.zeros(nbins, dtype=np.int64)
    dbl = ctypes.POINTER(ctypes.c_double)
    _LIB.count(
        pos.ctypes.data_as(dbl),
        len(pos),
        edges.ctypes.data_as(dbl),
        nbins,
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_longlong)),
    )
    if nbins and out[0] < 0:
        raise MemoryError("pairs.c could not allocate its work arrays")
    return out
