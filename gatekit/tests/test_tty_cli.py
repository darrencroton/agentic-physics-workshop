import os
import shutil
import subprocess
import sys
import unittest

from gatekit import ptyhelper, state as st
from tests import fakerepo

PY = sys.executable


class TtyTests(unittest.TestCase):
    def setUp(self):
        self.root = fakerepo.make()
        self.gate = os.path.join(self.root, "gate")

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_refuses_without_tty(self):
        for args in (["hint"], ["unlock"], ["skip", "--master"], ["reset"], ["allow-model", "sonnet"]):
            proc = subprocess.run([PY, self.gate] + args, cwd=self.root, capture_output=True,
                                  text=True, stdin=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 3, args)
            self.assertIn("for humans, in the gate terminal", proc.stderr)
        proc = subprocess.run([PY, self.gate, "status"], cwd=self.root, capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Level 0: Zero", proc.stdout)
        self.assertIn("Persona: literal", proc.stdout)

    def test_hint_through_pty(self):
        code, out = ptyhelper.run_pty([PY, self.gate, "hint"], cwd=self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("Hint 1 of 3", out)
        self.assertIn("Hint one for level 0", out)
        code, out = ptyhelper.run_pty([PY, self.gate, "hint"], cwd=self.root)
        self.assertEqual(code, 1)
        self.assertIn("unlocks after 5 minutes", out)
        state = st.load_state(self.root)
        self.assertEqual(state["levels"]["0"]["hints_used"], [0])
        with open(os.path.join(self.root, "LOG.md")) as fh:
            self.assertIn("Hint 1 used", fh.read())

    def test_reset_through_pty(self):
        state = st.load_state(self.root)
        st.advance_level(state, "coach")
        st.save_state(self.root, state)
        code, out = ptyhelper.run_pty([PY, self.gate, "reset"], [("level 0?", "y")], cwd=self.root)
        self.assertEqual(code, 0, out)
        self.assertEqual(st.load_state(self.root)["level"], 0)
        code, out = ptyhelper.run_pty([PY, self.gate, "reset"], [("level 0?", "n")], cwd=self.root)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
