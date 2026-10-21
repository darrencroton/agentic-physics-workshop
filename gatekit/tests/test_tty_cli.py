import contextlib
import io
import os
import shutil
import subprocess
import sys
import types
import unittest
from unittest import mock

from gatekit import cli, exercise, ptyhelper, state as st
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


class UnlockRenderTests(unittest.TestCase):
    @staticmethod
    def render(func, *args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            func(*args)
        return buffer.getvalue()

    def test_header_rule_matches_length(self):
        self.assertEqual(self.render(cli._header, "Level 1 unlocked: A"),
                         "Level 1 unlocked: A\n" + "-" * 19 + "\n")

    def test_closing_shows_note_then_talk_prompts(self):
        gate = {"note": "A note.", "talk": ["One?", "Two?"]}
        self.assertEqual(
            self.render(cli._closing, gate),
            "\nA note.\n\nTalk it over (30 seconds, nothing to type):\n  One?\n  Two?\n")
        self.assertIn("  Only?", self.render(cli._closing, {"talk": "Only?"}))
        self.assertEqual(self.render(cli._closing, {}), "")

    def test_check_notes_come_only_from_note_lines(self):
        self.assertEqual(cli._notes("noise\nNote: be kind.\nNote: again.\n"),
                         ["Note: be kind.", "Note: again."])


class QuestionTextTests(unittest.TestCase):
    QUESTION = {"id": "q", "prompt": "Static?", "wrong_hint": "Static hint.",
                "text_from": "tool.text"}

    def text(self, fn):
        tool = types.SimpleNamespace(questions={"text": fn})
        with mock.patch.object(cli, "_tool", return_value=tool):
            return cli._question_text("/root", {}, {}, self.QUESTION)

    def test_text_from_replaces_static_fields(self):
        self.assertEqual(self.text(lambda r, s, q: {"prompt": "Dynamic?", "wrong_hint": "Dynamic hint."}),
                         ("Dynamic?", "Dynamic hint."))
        self.assertEqual(self.text(lambda r, s, q: {"prompt": "Dynamic?", "wrong_hint": ""}),
                         ("Dynamic?", "Static hint."))

    def test_text_from_failure_falls_back_to_static(self):
        def broken(root, state, question):
            raise RuntimeError("no data")
        static = ("Static?", "Static hint.")
        self.assertEqual(self.text(broken), static)
        self.assertEqual(self.text(lambda r, s, q: None), static)
        with mock.patch.object(cli, "_tool", side_effect=exercise.ExerciseError("no tool")):
            self.assertEqual(cli._question_text("/root", {}, {}, self.QUESTION), static)


class HintTextTests(unittest.TestCase):
    TIER = {"text": "Static hint.", "text_from": "tool.text"}

    def text(self, fn):
        tool = types.SimpleNamespace(hints={"text": fn})
        with mock.patch.object(cli, "_tool", return_value=tool):
            return cli._hint_text("/root", {}, {}, self.TIER)

    def test_text_from_replaces_static_text(self):
        self.assertEqual(self.text(lambda r, s, t: " Dynamic hint. "), "Dynamic hint.")

    def test_text_from_failure_falls_back_to_static(self):
        def broken(root, state, tier):
            raise RuntimeError("no data")
        self.assertEqual(self.text(broken), "Static hint.")
        self.assertEqual(self.text(lambda r, s, t: ""), "Static hint.")
        self.assertEqual(self.text(lambda r, s, t: None), "Static hint.")
        with mock.patch.object(cli, "_tool", side_effect=exercise.ExerciseError("no tool")):
            self.assertEqual(cli._hint_text("/root", {}, {}, self.TIER), "Static hint.")


if __name__ == "__main__":
    unittest.main()
