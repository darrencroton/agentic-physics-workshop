#!/usr/bin/env python3
"""Crypto-gate check for Level 2, run by `gate check` from the repo root.

On failure: one sentence on stderr, exit 1.
On success: exactly {"level": 2, "ok": true} on stdout, exit 0.
"""

import os
import sys

GATEKIT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ROOT = os.path.dirname(GATEKIT_DIR)
sys.path.insert(0, GATEKIT_DIR)

from exploretool import gates  # noqa: E402

if __name__ == "__main__":
    sys.exit(gates.run_check(ROOT, 2, sys.stdout, sys.stderr))
