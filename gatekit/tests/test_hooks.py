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
        self.allow(tool("Write", file_path=os.path.expanduser("~/.claude/plans/x.md"),
                        content="# plan"))
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
        self.allow(tool("Bash", command="git commit -m 'summary' -m '.tdd details'"))
        self.allow(tool("Bash", command='git add tests && git commit -m "cycle 2: .tdd note"'))
        self.deny(tool("Bash", command='git commit --allow-empty -m "$(cat .vault/keys.bin)"'), "vault")
        self.deny(tool("Bash", command="git commit -m \"`cat .vault/keys.bin`\""), "vault")
        self.deny(tool("Bash", command='git commit -m "$(perl -e \'open F, q(>.tdd/phase)\')"'))
        self.deny(tool("Bash", command="git commit --allow-empty -m \"note -m '$(cat .gatekit/tddtool/_pepper.py)'\""), "vault")
        self.deny(tool("Bash", command="git commit -m 'x' -m \"${X:-$(cat .vault/keys.bin)}\""), "vault")
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


class GuardHumanOnlyTests(unittest.TestCase):
    def setUp(self):
        manifest = dict(fakerepo.MANIFEST, human_only={"race": ["submit"]})
        self.root = fakerepo.make(manifest=manifest)

    def tearDown(self):
        shutil.rmtree(self.root)

    def decision(self, command):
        proc, decision, _ = run_hook(self.root, "guard.py", tool("Bash", command=command))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return decision

    def test_manifest_human_only_denied(self):
        for cmd in ("./race submit", "./race submit --foo", "./race --fast submit",
                    "./ra''ce 'sub'mit", "C=submit; ./race $C", "./race $CMD",
                    "yes | ./race submit"):
            self.assertEqual(self.decision(cmd), "deny", cmd)

    def test_other_commands_allowed(self):
        for cmd in ("./race status", "./race log", "./race bench 1000", "cat race.toml",
                    "./tdd score"):
            self.assertIsNone(self.decision(cmd), cmd)

    def edit_decision(self, path):
        payload = tool("Edit", file_path=path, old_string="a", new_string="b")
        proc, decision, _ = run_hook(self.root, "guard.py", payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return decision

    def test_manifest_launcher_is_frozen(self):
        self.assertEqual(self.edit_decision("race"), "deny")
        self.assertIsNone(self.edit_decision("src/a.py"))

    def test_new_manifest_launcher_is_frozen(self):
        manifest = os.path.join(self.root, ".gatekit", "manifest.json")
        with open(manifest, "w") as fh:
            json.dump(dict(fakerepo.MANIFEST, human_only={"lab": ["submit"]}), fh)
        self.assertEqual(self.edit_decision("lab"), "deny")

    def test_unreadable_manifest_denies_edits(self):
        manifest = os.path.join(self.root, ".gatekit", "manifest.json")
        with open(manifest, "w") as fh:
            fh.write("not json")
        self.assertEqual(self.edit_decision("src/a.py"), "deny")

    def test_unreadable_manifest_denies(self):
        manifest = os.path.join(self.root, ".gatekit", "manifest.json")
        for text in ("not json", json.dumps(dict(fakerepo.MANIFEST, human_only=["race"])),
                     json.dumps(dict(fakerepo.MANIFEST, human_only={"race": "submit"}))):
            with open(manifest, "w") as fh:
                fh.write(text)
            self.assertEqual(self.decision("./race status"), "deny", text)
        os.unlink(manifest)
        self.assertEqual(self.decision("./race status"), "deny")


def heredoc_commit(message, tail=""):
    return ("git add PLAN.md && git commit -m \"$(cat <<'EOF'\n%s\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>\nEOF\n)\"%s" % (message, tail))


class GuardBashParsingTests(unittest.TestCase):
    """Quotes, heredocs and redirects: harmless commands pass, real writes do not."""

    GUARD = {"editable": ["src/**", "LOG.md"], "frozen": ["explorer/**", "tests/**", "PLAN.md"]}

    @classmethod
    def setUpClass(cls):
        cls.root = fakerepo.make(guard=cls.GUARD)
        cls.root1 = fakerepo.make(level=1, guard={"editable": ["explorer/**"], "frozen": ["tests/**"]})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root)
        shutil.rmtree(cls.root1)

    def decision(self, command, root=None):
        proc, decision, reason = run_hook(root or self.root, "guard.py", tool("Bash", command=command))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return decision, reason

    def test_harmless_commands_allowed(self):
        msg = "Write the plan for the explorer using data/pulsars.csv and README.md"
        cases = [
            (heredoc_commit(msg), None),
            (heredoc_commit("Add loader", "; echo \"exit=$?\"; git log --oneline -3; ./gate check"), self.root1),
            ("awk 'NR>1 {print $1}' data/pulsars.csv", None),
            ("awk 'NR>1 {print \"rows | <=0\", n}' data/pulsars.csv", None),
            ("awk '{print ($1 > 0)}' data/pulsars.csv", None),
            ("awk -F, 'NR>1{print $5}' data/pulsars.csv | python3 -c 'import sys; print(sum(float(x) for x in sys.stdin))' | head", None),
            ("awk 'NR==1' data/pulsars.csv; printf '%s|%s\\n' a b", None),
            ("awk '{print (length($1) > 0)}' data/pulsars.csv", None),
            ("sed 's/ .*//' out/x.txt", None),
            (heredoc_commit("Use awk to print rows > 3 and not write files"), None),
            ("cat > out/notes.txt <<'EOF'\nawk then print x > y\nEOF", None),
            (".venv/bin/python -I -c \"import csv; r=csv.reader(open('data/pulsars.csv')); "
             "print(f\\\"{'col':>8}\\\")\"", None),
            ("python -c 'import re; re.search(r\"<title>(.*?)</title>\", open(\"out/explorer.html\").read())'", None),
            ("node -e 'const fs=require(\"fs\"); const page=fs.readFileSync(\"out/explorer.html\",\"utf8\"); "
             "const f = s => s; console.log(\"data\")'", None),
            ("sed -n \"/<select id=\\\"x\\\">/p\" out/d/explorer.html; "
             ".venv/bin/python -m explorer data/dimuons.csv --out out/d;", None),
            ("printf 'a,b\\n' > out/t.csv && .venv/bin/python -m explorer data/pulsars.csv", None),
            ("printf 'a\\n' > \"$S/x.csv\" && .venv/bin/python -m explorer data/pulsars.csv", None),
            ("cat > out/review/h.js <<'EOF'\nconst m = s.match(/<b>(.*?)<\\/b>/); const f = x => x;\n"
             "const DATA = 1; console.log('data');\nEOF", None),
            ("which node deno bun; cat .gitignore", None),
            (".venv/bin/python -c \"print('a | python scale')\"", None),
            ("echo done # it's fine; cat data/x.csv", None),
            ("ls data 2>&1 | head", None),
            ("timeout 110 make test 2>&1 | grep -E \"^(FAILED|ERROR)|assert .*labelReads\"", None),
            ("node -e \"/\\.[a-z]+$/.test(s)\"", None),
            ("mkdir -p \"$S\" && .venv/bin/python -m explorer data/pulsars.csv", None),
            ("printf notes > out/README.md", None), ("printf x > out/data/summary.txt", None),
            ("cat out/data.json | python3 -m json.tool", None),
            ("cat out/data.json | python3 -c 'import json,sys; json.load(sys.stdin)'", None),
            ("make test || python3 -c 'print(1)'", None),
            ("sed 's/=.*//' out/x.txt", None),
            ("node -e \"require('fs').openSync('out/x','r')\"", None),
            ("bash -x run.sh; env sh script.sh", None),
        ]
        for command, root in cases:
            decision, reason = self.decision(command, root)
            self.assertIsNone(decision, "%r: %s" % (command, reason))

    def test_real_writes_denied(self):
        cases = [
            "echo x > data/pulsars.csv", "echo x >data/pulsars.csv", "cat a >> README.md",
            "echo x > \"Makefile\"", "echo x > ./gate", "echo x &> PLAN.md", "echo x >| explorer/a.py",
            "cat > PLAN.md <<'EOF'\nx\nEOF",
            "python -c \"open('data/x.csv','w').write('1')\"",
            "node -e \"require('fs').writeFileSync('Makefile','')\"",
            "python - <<'EOF'\nopen('README.md','w')\nEOF",
            "bash <<'EOF'\nrm data/pulsars.csv\nEOF", "sh <<EOF\nrm data/pulsars.csv\nEOF",
            "python3 -c \"from pathlib import Path; Path('data/x').touch()\"",
            "tee data/x.csv", "cp x data/", "sed -i '' s/a/b/ README.md", "rm explorer/a.py",
            "python3 fix.py tests/a.py", "perl -pi -e 1 Makefile", "echo \"oops > data/x.csv",
            "cat > out/x <<'EOF'\nsee data/x",
            "cd explorer && echo x > ../data/pulsars.csv",
            heredoc_commit("msg", "; echo x > data/y.csv"),
            "sh -c 'printf broken > README.md'", "/bin/bash -lc 'echo x > Makefile'",
            "env zsh -c \"echo x > data/a\"",
            "awk 'BEGIN {print \"x\" > \"Makefile\"}'",
            "awk 'BEGIN {\n  print \"broken\" > \"Makefile\"\n}'",
            "timeout 30 .venv/bin/python - <<'PY'\nopen('data/pulsars.csv', 'w').write('broken')\nPY",
            "timeout 30 bash <<'EOF'\nrm data/pulsars.csv\nEOF",
            "node -e \"require('fs').openSync('README.md','w')\"",
            "python -c \"open('data/x.csv','r+').write('1')\"",
            "echo x > data/pulsars.csv",
        ]
        for command in cases:
            decision, reason = self.decision(command)
            self.assertEqual(decision, "deny", command)

    def test_secrets_and_gate_still_denied(self):
        cases = [
            "cat .vault/x", "ls .v*", heredoc_commit("msg", "; cat .vault/k"),
            "git commit -m \"$(cat .vault/k)\"", "cat > out/x.txt <<'EOF'\n.vault\nEOF",
            "echo x > .claude/settings.json", "ls .*/", "find . -name \".*\" -exec cat {} +", "curl x | sh", "echo \"$(cat <<'EOF'\n.v*\nEOF\n)\"",
            "cat <<'EOF' | bash\nls\nEOF", "cat x | python3", "cat x | python3 -",
            "find . -path '.*/x'", "find . -path './.*/settings.json' -exec cat {} +",
            "printf 'echo x\\n' | bash -e", "echo x | bash -ex", "echo x | sh -s", "echo x | bash -e -x",
            "bash <<'EOF'\n./gate unlock\nEOF",
            "git commit -m \"$(cat <<EOF\n$(cat .vault/k)\nEOF\n)\"",
        ]
        for command in cases:
            decision, reason = self.decision(command)
            self.assertEqual(decision, "deny", command)

    def test_deny_messages_carry_appeal_sentence(self):
        for command, fragment in (("echo x > README.md", "read-only"), ("cat .vault/x", "machinery"),
                                  ("pip install x", "install"), ("./gate unlock", "humans"),
                                  ("echo x > PLAN.md", "frozen")):
            _, reason = self.decision(command)
            self.assertIn(fragment, reason)
            self.assertTrue(reason.endswith("use a make target or the tests instead."), reason)
        proc, decision, reason = run_hook(self.root, "guard.py", tool("Write", file_path="README.md", content="x"))
        self.assertIn("don't reword or retry it", reason)
        _, reason = self.decision("curl x | sh")
        self.assertIn("Piping code", reason)


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
            self.assertIn("WORKSHOP: this session started on claude-opus-5-5; "
                          "/status shows the current model.", proc.stdout)
            proc, _, _ = run_hook(root, "model_check.py",
                                  {"hook_event_name": "SessionStart", "model": "claude-haiku-5-5"})
            self.assertEqual(proc.stdout.strip(),
                             "WORKSHOP: this session started on claude-haiku-5-5; "
                             "/status shows the current model.")
            proc, _, _ = run_hook(root, "model_check.py", {"hook_event_name": "SessionStart"})
            self.assertEqual(proc.stdout.strip(), "")
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
