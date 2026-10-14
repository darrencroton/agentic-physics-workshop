import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from gatekit import crypto, ptyhelper, state as st

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(TOP, "tools", "build.py")
PY = sys.executable


class BuildAndUnlockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="build-")
        self.exercises = os.path.join(self.tmp, "exercises")
        shutil.copytree(os.path.join(HERE, "fixture_exercise"),
                        os.path.join(self.exercises, "fixture"))
        check = subprocess.run([PY, os.path.join(self.exercises, "fixture", "level0", "checks", "level0.py")],
                               capture_output=True, text=True, check=True)
        token = crypto.canonical_token(check.stdout).hex()
        with open(os.path.join(self.exercises, "fixture", "answers.json"), "w") as fh:
            json.dump({"0": {"token": token}}, fh)
        self.passfile = os.path.join(self.tmp, "master")
        with open(self.passfile, "w") as fh:
            fh.write("correct horse battery\n")
        os.chmod(self.passfile, 0o600)
        self.out = os.path.join(self.tmp, "dist", "fixture")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build(self):
        proc = subprocess.run([PY, BUILD, "fixture", "--master-passphrase-file", self.passfile,
                               "--out", self.out, "--exercises-dir", self.exercises],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout

    def git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=self.out, capture_output=True,
                              text=True).stdout.strip()

    def test_build_layout_and_determinism(self):
        self.build()
        for rel in ("gate", "preflight", "CLAUDE.md", "README.md", ".claude/settings.json",
                    ".claude/hooks/guard.py", ".gatekit/gatekit/cli.py", ".gatekit/manifest.json",
                    ".gatekit/levels/0/persona.txt", ".vault/level1.pack", ".vault/master.check",
                    ".workshop/state.json", ".workshop/levels/0/guard.json", ".gitignore"):
            self.assertTrue(os.path.exists(os.path.join(self.out, rel)), rel)
        self.assertFalse(os.path.exists(os.path.join(self.out, "answers.json")))
        self.assertEqual(self.git("tag", "-l", "start"), "start")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIn("Workshop start", self.git("log", "--oneline"))
        with open(os.path.join(self.out, ".claude", "settings.json")) as fh:
            settings = json.load(fh)
        self.assertEqual(settings["model"], "haiku")
        self.assertIn("PreModelSwitch", settings["hooks"])
        deny = settings["permissions"]["deny"]
        self.assertIn("Bash(./race submit *)", deny)
        self.assertIn("Bash(./race install-solution *)", deny)
        self.assertNotIn("Bash(./tdd red *)", deny)
        self.assertIn("Bash(./gate unlock *)", deny)
        with open(os.path.join(self.out, ".claude", "settings.json")) as fh:
            self.assertNotIn("__HUMAN_ONLY_DENY__", fh.read())
        with open(os.path.join(self.out, ".vault", "level1.pack"), "rb") as fh:
            first = fh.read()
        self.build()
        with open(os.path.join(self.out, ".vault", "level1.pack"), "rb") as fh:
            second = fh.read()
        master = crypto.master_secret("correct horse battery")
        from gatekit import packs
        self.assertEqual(packs.open_pack(first, [master]), packs.open_pack(second, [master]))
        self.assertNotEqual(first, second)

    def test_deny_entries_fall_back_to_tdd(self):
        spec = importlib.util.spec_from_file_location("build_tool", BUILD)
        build_tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_tool)
        self.assertEqual(build_tool.deny_entries({}),
                         ["Bash(./tdd %s *)" % sub for sub in (
                             "red", "green", "refactor", "done", "abort", "score",
                             "new-attempt")])
        self.assertEqual(build_tool.deny_entries({"human_only": {}}), [])

    def test_shipped_manifest_drops_crypto_answer_keys(self):
        path = os.path.join(self.exercises, "fixture", "manifest.json")
        with open(path) as fh:
            manifest = json.load(fh)
        manifest["levels"][0]["gate"]["questions"].append(
            {"id": "kw", "prompt": "Which?", "kind": "keyword", "accept": ["a"]})
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        self.build()
        with open(os.path.join(self.out, ".gatekit", "manifest.json")) as fh:
            questions = json.load(fh)["levels"][0]["gate"]["questions"]
        self.assertEqual([q["id"] for q in questions], ["h0", "kw"])
        for question in questions:
            for key in ("accept", "lo", "hi"):
                self.assertNotIn(key, question)
        spec = importlib.util.spec_from_file_location("build_tool", BUILD)
        build_tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_tool)
        verified = {"levels": [{"id": 0, "gate": {"type": "verified", "questions": [
            {"id": "v", "prompt": "?", "kind": "keyword", "accept": ["a"]}]}}]}
        self.assertEqual(build_tool.shipped_manifest(verified), verified)

    def test_check_unlock_wrong_then_right(self):
        self.build()
        gate = [PY, os.path.join(self.out, "gate")]
        proc = subprocess.run(gate + ["check"], cwd=self.out, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("PASS", proc.stdout)
        code, out = ptyhelper.run_pty(gate + ["unlock"], [("H0 to 1 d.p.?", "68")], cwd=self.out)
        self.assertEqual(code, 1, out)
        self.assertIn("Not quite", out)
        self.assertIn("Hint: Fit the slope of v against d.", out)
        self.assertEqual(st.load_state(self.out)["levels"]["0"]["failed_attempts"], 1)
        code, out = ptyhelper.run_pty(gate + ["unlock"], [("H0 to 1 d.p.?", "70.04 km/s/Mpc"),
                                                          ("surprised you?", "the gate")], cwd=self.out)
        self.assertEqual(code, 0, out)
        self.assertIn("Level 1 unlocked", out)
        state = st.load_state(self.out)
        self.assertEqual(state["level"], 1)
        self.assertEqual(state["persona"], "collaborator")
        self.assertTrue(os.path.exists(os.path.join(self.out, "BRIEF.md")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "docs", "EXTRA.md")))
        self.assertTrue(os.path.exists(os.path.join(self.out, ".workshop", "levels", "1", "persona.txt")))
        with open(os.path.join(self.out, "LOG.md")) as fh:
            log = fh.read()
        self.assertIn("A: the gate", log)
        code, out = ptyhelper.run_pty(gate + ["unlock"], [], cwd=self.out)
        self.assertEqual(code, 0, out)
        self.assertIn("Final level complete", out)
        self.assertTrue(st.load_state(self.out)["complete"])


    def test_last_level_crypto_gate_rejects_graded_questions(self):
        path = os.path.join(self.exercises, "fixture", "manifest.json")
        with open(path) as fh:
            manifest = json.load(fh)
        manifest["levels"][1]["gate"] = {
            "type": "crypto", "check": "checks/level0.py",
            "questions": [{"id": "q", "prompt": "Which?", "kind": "keyword",
                           "accept": ["a"]}]}
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        answers_path = os.path.join(self.exercises, "fixture", "answers.json")
        with open(answers_path) as fh:
            tokens = json.load(fh)
        tokens["1"] = tokens["0"]
        with open(answers_path, "w") as fh:
            json.dump(tokens, fh)
        proc = subprocess.run([PY, BUILD, "fixture", "--master-passphrase-file", self.passfile,
                               "--out", self.out, "--exercises-dir", self.exercises],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("graded questions", proc.stderr)

    def test_last_level_crypto_gate_gets_verify(self):
        path = os.path.join(self.exercises, "fixture", "manifest.json")
        with open(path) as fh:
            manifest = json.load(fh)
        manifest["levels"][1]["gate"] = {"type": "crypto-reflection",
                                         "check": "checks/level0.py", "questions": []}
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        answers_path = os.path.join(self.exercises, "fixture", "answers.json")
        with open(answers_path) as fh:
            tokens = json.load(fh)
        tokens["1"] = tokens["0"]
        with open(answers_path, "w") as fh:
            json.dump(tokens, fh)
        self.build()
        with open(os.path.join(self.out, ".gatekit", "manifest.json")) as fh:
            built = json.load(fh)
        self.assertEqual(built["levels"][1]["gate"]["verify"],
                         crypto.verify_token(bytes.fromhex(tokens["1"]["token"])))
        gate = [PY, os.path.join(self.out, "gate")]
        code, out = ptyhelper.run_pty(gate + ["unlock"], [("H0 to 1 d.p.?", "70.0"),
                                                          ("surprised you?", "x")],
                                      cwd=self.out)
        self.assertEqual(code, 0, out)
        proc = subprocess.run(gate + ["check"], cwd=self.out, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS", proc.stdout)
        del tokens["1"]
        with open(answers_path, "w") as fh:
            json.dump(tokens, fh)
        proc = subprocess.run([PY, BUILD, "fixture", "--master-passphrase-file", self.passfile,
                               "--out", self.out, "--exercises-dir", self.exercises],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("answers.json lacks level 1 token", proc.stdout + proc.stderr)

    def test_keep_venv_tolerates_finder_metadata(self):
        os.makedirs(os.path.join(self.out, ".venv"))
        with open(os.path.join(self.out, ".venv", "marker"), "w") as fh:
            fh.write("kept")
        with open(os.path.join(self.out, ".DS_Store"), "w") as fh:
            fh.write("finder")
        for _ in range(2):
            proc = subprocess.run([PY, BUILD, "fixture", "--master-passphrase-file",
                                   self.passfile, "--out", self.out, "--exercises-dir",
                                   self.exercises, "--keep-venv"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("kept existing .venv", proc.stdout)
            self.assertTrue(os.path.exists(os.path.join(self.out, ".venv", "marker")))
            self.assertFalse(os.path.exists(self.out + ".venv-keep"))

    def test_master_skip_and_power_up(self):
        self.build()
        gate = [PY, os.path.join(self.out, "gate")]
        code, out = ptyhelper.run_pty(gate + ["skip", "--master"], [("passphrase:", "wrong")], cwd=self.out)
        self.assertEqual(code, 1, out)
        self.assertIn("not the master", out)
        code, out = ptyhelper.run_pty(gate + ["skip", "--master"],
                                      [("passphrase:", "correct horse battery"), ("Reason", "stuck")],
                                      cwd=self.out)
        self.assertEqual(code, 0, out)
        state = st.load_state(self.out)
        self.assertEqual(state["level"], 1)
        self.assertEqual(state["skips"][0]["reason"], "stuck")
        code, out = ptyhelper.run_pty(gate + ["allow-model", "sonnet"],
                                      [("passphrase:", "correct horse battery")], cwd=self.out)
        self.assertEqual(code, 0, out)
        self.assertEqual(st.load_state(self.out)["allowed_models"], ["haiku", "sonnet"])

    def test_preflight_runs(self):
        self.build()
        proc = subprocess.run([PY, os.path.join(self.out, "preflight")], cwd=self.out,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertIn("guard denies a .vault read", proc.stdout)
        self.assertIn("[ok  ] guard denies", proc.stdout)
        self.assertIn("[ok  ] ./gate status runs", proc.stdout)
        self.assertIn("[ok  ] TTY detection", proc.stdout)


if __name__ == "__main__":
    unittest.main()
