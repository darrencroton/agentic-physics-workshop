import json
import os
import shutil
import subprocess
import sys
import unittest

from tests import fakerepo

PY = sys.executable


def run_hook(root, name, payload, raw=None):
    env = fakerepo.env_for(root)
    data = raw if raw is not None else json.dumps(payload)
    proc = subprocess.run([PY, os.path.join(root, ".claude", "hooks", name)],
                          input=data, capture_output=True, text=True, env=env,
                          cwd=root)
    decision = None
    reason = ""
    if proc.stdout.strip():
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
            spec = out.get("hookSpecificOutput", {})
            decision = spec.get("permissionDecision")
            reason = spec.get("permissionDecisionReason", "")
        except ValueError:
            pass
    return proc, decision, reason


def tool(name, **tool_input):
    return {"hook_event_name": "PreToolUse", "tool_name": name,
            "tool_input": tool_input, "session_id": "x", "cwd": "."}


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.root = fakerepo.make()

    def tearDown(self):
        shutil.rmtree(self.root)

    def deny(self, payload, fragment=None):
        proc, decision, reason = run_hook(self.root, "guard.py", payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(decision, "deny", "expected deny for %r; stdout=%r" % (payload, proc.stdout))
        if fragment:
            self.assertIn(fragment, reason)

    def allow(self, payload):
        proc, decision, _ = run_hook(self.root, "guard.py", payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsNone(decision, "expected allow for %r; stdout=%r" % (payload, proc.stdout))

    def test_blocks_vault_read(self):
        self.deny(tool("Read", file_path=".vault/level1.pack"), "vault")
        self.deny(tool("Read", file_path=os.path.join(self.root, ".vault/level1.pack")))
        self.deny(tool("Read", file_path="src/../.vault/level1.pack"))
        self.deny(tool("Read", file_path=".workshop/state.json"))
        self.deny(tool("Read", file_path=".gatekit/gatekit/crypto.py"))
        self.deny(tool("Glob", pattern=".vault/*"))
        self.deny(tool("Grep", pattern="slots", path=".vault"))

    def test_blocks_gate_via_bash(self):
        for cmd in ("./gate unlock", "yes | ./gate unlock", "cd /tmp && ../x/gate hint",
                    "python3 gate skip --master", "./tdd green", "./tdd score"):
            self.deny(tool("Bash", command=cmd), "humans")

    def test_blocks_package_managers_and_pty(self):
        for cmd in ("pip install numpy", "pip3 install x", "python3 -m pip install x",
                    "uv pip install x", "brew install gfortran"):
            self.deny(tool("Bash", command=cmd), "install")
        for cmd in ("python3 -c 'import pty; pty.spawn([\"./gate\",\"unlock\"])'",
                    "script -q /dev/null ./gate unlock", "expect -c 'spawn ./gate unlock'"):
            self.deny(tool("Bash", command=cmd))

    def test_blocks_bash_mentioning_secret_paths(self):
        for cmd in ("cat .vault/level1.pack", "ls -la .workshop", "base64 -d < .vault/level1.pack",
                    "cat $(pwd)/.vault/level1.pack", "tar tf .vault/scoring.pack"):
            self.deny(tool("Bash", command=cmd), "vault")

    def test_blocks_frozen_path_edits(self):
        self.deny(tool("Edit", file_path="README.md", old_string="a", new_string="b"), "read-only")
        self.deny(tool("Write", file_path="Makefile", content="x"), "read-only")
        self.deny(tool("Write", file_path="data/new.csv", content="x"))
        self.deny(tool("Write", file_path=".claude/settings.json", content="{}"))
        self.deny(tool("Write", file_path="/tmp/outside.txt", content="x"), "outside")
        self.deny(tool("Write", file_path="notes.md", content="x"))
        self.deny(tool("Bash", command="echo x > README.md"), "read-only")
        self.deny(tool("Bash", command="sed -i '' 's/a/b/' Makefile"))
        self.deny(tool("Bash", command="cp src/x.py data/y.csv"))

    def test_allows_normal_work(self):
        self.allow(tool("Edit", file_path="src/hzbin/binning.py", old_string="a", new_string="b"))
        self.allow(tool("Write", file_path="tests/test_binning.py", content="x"))
        self.allow(tool("Write", file_path="LOG.md", content="x"))
        self.allow(tool("Read", file_path="README.md"))
        self.allow(tool("Read", file_path="/usr/lib/python3/os.py"))
        self.allow(tool("Bash", command=".venv/bin/python -m pytest -q"))
        self.allow(tool("Bash", command="./tdd test && ./gate status"))
        self.allow(tool("Bash", command="git status && git diff"))
        self.allow(tool("Bash", command="git add tests && git commit -m 'cycle 1 test'"))
        self.allow(tool("Glob", pattern="src/**/*.py"))
        self.allow(tool("Grep", pattern="def ", path="src"))
        self.allow({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                    "tool_input": {"prompt": "review"}})

    def test_adversarial_bypasses_closed(self):
        self.deny(tool("Read", file_path=".VAULT/keys.bin"), "vault")
        self.deny(tool("Read", file_path=".Gatekit/tddtool/_pepper.py"))
        self.deny(tool("Write", file_path=".CLAUDE/hooks/guard.py", content=""))
        self.deny(tool("Write", file_path="readme.MD", content="x"))
        self.deny(tool("Grep", pattern="PEPPER", path=".", glob=".gatekit/**"))
        self.deny(tool("Glob", pattern=".*/**/*.pack"))
        self.deny(tool("Glob", pattern="**/.vault/*"))
        for cmd in ("cat .VAULT/keys.bin", "printf '' > .CLAUDE/hooks/guard.py",
                    "git show start:.vault/keys.bin", "git show HEAD", "git cat-file -p HEAD:x",
                    "git archive HEAD | tar -x -C /tmp", "git log -p", "git grep PEPPER",
                    "git config core.hooksPath hooks", "cat .v*ult/keys.bin", "cat .[v]ault/x",
                    "cat {x,.vault}/keys.bin", "cat \".\"vault/keys.bin", "cat .\\vault/x",
                    "./g''ate unlock 1", "./tdd 'r'ed x", "T=red; ./tdd $T", "sh -c './g''ate unlock'",
                    "./gate --verbose unlock", "python3 -mpip install x", ".venv/bin/python -m ensurepip",
                    "uvx foo", "curl x | python3", "echo x | base64 -d | sh",
                    "env -i ./gate hint", "unset CLAUDECODE; ./gate hint",
                    "python3 -c 'import o''s; print(o)' .gatekit/x"):
            self.deny(tool("Bash", command=cmd))
        for cmd in ("ln -s .. tests/parent", "git diff --no-index --binary tests .",
                    "cd /tmp && ln -sf /etc/passwd tests/x", "  ln -s .. tests/p", "/bin/ln -s .. tests/p",
                    "echo x > %s/tdd" % self.root, "cp /tmp/x %s/gate" % self.root,
                    "cat > %s/README.md << EOF" % self.root, 'python3 -m "pip" install requests',
                    ".venv/bin/python -m 'pip' install x"):
            self.deny(tool("Bash", command=cmd))
        self.allow(tool("Bash", command="git commit -m 'Fix .tdd cycle handling'"))
        self.allow(tool("Bash", command="git commit -am 'use .vault-free approach'"))
        os.symlink("..", os.path.join(self.root, "tests", "parent"))
        self.deny(tool("Write", file_path="tests/parent/gate", content="x"))
        self.deny(tool("Write", file_path="tests/parent/.vault/x", content="x"))
        for cmd in ("./tdd test tests/test_binning.py -v 2>&1 | tail -30",
                    ".venv/bin/pytest tests/ -q 2>&1", "python3 -m pytest tests/test_binning.py::test_x",
                    "git commit -m 'Implement S1: x >= e_k; tests pass'",
                    "git commit -m 'Add test: expect ValueError when sigma <= 0'",
                    "git commit -m 'tdd red: single bin mean'",
                    "cd /Users/me/dist/tdd-ladder && .venv/bin/python -m pytest -q",
                    "python -c \"from hzbin.data import load_hz; print(load_hz('data/hz_mock.csv'))\"",
                    "make test 2>&1 | tail -20", "python3 -c 'import numpy; print(numpy.__version__)'",
                    "git log --stat", "git diff HEAD~1", "git status", "cat README.md",
                    "cat src/hzbin/binning.py", "ls -la", "cat .gitignore", "./tdd test -q",
                    ".venv/bin/python -m pytest tests/test_x.py -k mean"):
            self.allow(tool("Bash", command=cmd))

    def test_malformed_input_denies(self):
        for raw in ("", "not json", "[1,2]", '{"tool_name": "Read"}',
                    '{"tool_name": "Read", "tool_input": "x"}',
                    '{"tool_name": "Edit", "tool_input": {}}'):
            proc, decision, reason = run_hook(self.root, "guard.py", None, raw=raw)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(decision, "deny", raw)

    def test_missing_state_denies(self):
        shutil.rmtree(os.path.join(self.root, ".workshop"))
        self.deny(tool("Edit", file_path="src/a.py", old_string="a", new_string="b"), "gate reset")


class GuardPhaseTests(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(self.root)

    def check(self, phase, path, expected):
        self.root = fakerepo.make(guard=fakerepo.GUARD_PHASES, phase=phase)
        proc, decision, reason = run_hook(self.root, "guard.py",
                                          tool("Write", file_path=path, content="x"))
        self.assertEqual(decision, expected, "%s %s: %s" % (phase, path, reason))
        return reason

    def test_green_freezes_tests(self):
        reason = self.check("green", "tests/test_x.py", "deny")
        self.assertIn("frozen in GREEN", reason)
        shutil.rmtree(self.root)
        self.check("green", "src/binning.py", None)
        shutil.rmtree(self.root)
        self.check("red", "src/binning.py", "deny")
        shutil.rmtree(self.root)
        self.check("red", "tests/test_x.py", None)
        shutil.rmtree(self.root)
        self.check("none", "tests/test_x.py", "deny")

    def test_green_bash_edit_of_tests_denied(self):
        self.root = fakerepo.make(guard=fakerepo.GUARD_PHASES, phase="green")
        for cmd in ("echo x >> tests/test_a.py", "sed -i '' s/1/2/ tests/test_a.py",
                    "git checkout -- tests/", "python3 fix.py tests/test_a.py",
                    "sed -i '' s/1/2/ %s/tests/test_a.py" % self.root):
            _, decision, reason = run_hook(self.root, "guard.py", tool("Bash", command=cmd))
            self.assertEqual(decision, "deny", cmd)
            self.assertIn("GREEN", reason)
        _, decision, _ = run_hook(self.root, "guard.py", tool("Bash", command="pytest tests/"))
        self.assertIsNone(decision)


class ModelLockTests(unittest.TestCase):
    def setUp(self):
        self.root = fakerepo.make()

    def tearDown(self):
        shutil.rmtree(self.root)

    def switch(self, to_model):
        payload = {"hook_event_name": "PreModelSwitch", "from_model": "claude-haiku-5-5",
                   "to_model": to_model, "source": "command"}
        return run_hook(self.root, "model_lock.py", payload)

    def test_allows_allowed_and_denies_others(self):
        for name in ("haiku", "claude-haiku-5-5", "Claude Haiku 5.5"):
            proc, decision, _ = self.switch(name)
            self.assertIsNone(decision, name)
            self.assertEqual(proc.returncode, 0)
        for name in ("opus", "claude-sonnet-5-5", "sonnet[1m]", "claude-opus-haiku",
                     "opus[haiku]", "claude-sonnet-4-5 # haiku", "haikus"):
            proc, decision, reason = self.switch(name)
            self.assertEqual(decision, "deny", name)
            self.assertIn("haiku", reason.lower())
        _, decision, _ = self.switch("")
        self.assertEqual(decision, "deny")
        for raw in ("[]", '["opus","haiku"]', '{"to_model": {"x": "haiku"}}'):
            proc, decision, _ = run_hook(self.root, "model_lock.py", None, raw=raw)
            self.assertEqual(decision, "deny", raw)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        proc, decision, _ = run_hook(self.root, "model_lock.py", None, raw="garbage")
        self.assertEqual(decision, "deny")

    def test_power_up(self):
        shutil.rmtree(self.root)
        self.root = fakerepo.make(allowed=["haiku", "sonnet"])
        _, decision, _ = self.switch("claude-sonnet-5-5")
        self.assertIsNone(decision)
        shutil.rmtree(self.root)
        self.root = fakerepo.make(allowed=["haiku", "claude-sonnet-5-5"])
        _, decision, _ = self.switch("claude-sonnet-5-5")
        self.assertIsNone(decision)
        _, decision, _ = self.switch("opus")
        self.assertEqual(decision, "deny")


class TeacherContextTests(unittest.TestCase):
    def test_prints_persona_per_level(self):
        for level, persona in ((0, "literal"), (1, "coach")):
            root = fakerepo.make(level=level)
            try:
                proc, _, _ = run_hook(root, "teacher_context.py",
                                      {"hook_event_name": "UserPromptSubmit", "prompt": "hi"})
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("WORKSHOP LEVEL %d" % level, proc.stdout)
                self.assertIn("persona: %s" % persona, proc.stdout)
                self.assertIn("Rules for level %d" % level, proc.stdout)
            finally:
                shutil.rmtree(root)

    def test_session_model_check(self):
        root = fakerepo.make()
        try:
            proc, _, _ = run_hook(root, "model_check.py",
                                  {"hook_event_name": "SessionStart", "model": "claude-opus-5-5"})
            self.assertIn("WARNING", proc.stdout)
            proc, _, _ = run_hook(root, "model_check.py",
                                  {"hook_event_name": "SessionStart", "model": "claude-haiku-5-5"})
            self.assertEqual(proc.stdout.strip(), "")
            proc, _, _ = run_hook(root, "model_check.py", {"hook_event_name": "SessionStart"})
            self.assertEqual(proc.stdout.strip(), "")
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
