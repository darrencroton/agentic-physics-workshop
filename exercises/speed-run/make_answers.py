#!/usr/bin/env python3
"""Write exercises/speed-run/answers.json: the crypto-gate tokens for levels 0-2.

Each level check prints exactly gates.success_line(N) on success. The gate
hashes the captured stdout with gatekit.crypto.canonical_token, so the token
here is that hash of the same text. Run with any python3 (stdlib only).
"""

import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.realpath(__file__))
TOP = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(TOP, "gatekit"))
sys.path.insert(0, os.path.join(HERE, "workshop"))

from gatekit import crypto  # noqa: E402
from racetool import gates  # noqa: E402

CRYPTO_LEVELS = (0, 1, 2)


def main():
    answers = {}
    for level in CRYPTO_LEVELS:
        line = gates.success_line(level)
        expected = json.dumps({"level": level, "ok": True}, sort_keys=True) + "\n"
        if line != expected:
            raise SystemExit("level %d check output %r differs from the contract %r"
                             % (level, line, expected))
        answers[str(level)] = {"token": crypto.canonical_token(line).hex()}
    path = os.path.join(HERE, "answers.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(answers, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % path)
    for level in CRYPTO_LEVELS:
        print("  level %d: %s" % (level, answers[str(level)]["token"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
