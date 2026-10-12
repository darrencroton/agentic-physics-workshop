"""Sample entry: the Level 3 C counter built with clang's default contraction.

Identical to the Level 3 solution except that -ffp-contract=off is missing:
pairs.c is compiled with clang -O2 -shared -fPIC, so clang fuses
dx*dx + dy*dy + dz*dz into FMA and a few pairs within an ulp of a bin edge
move bin. Exact on most data; fails exact on the hidden catalogue.
"""

import ctypes
import hashlib
import shutil
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pairs.c"
FLAGS = ["-O2", "-shared", "-fPIC"]


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
