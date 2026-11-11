import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from gatekit import sandbox as sb


class SandboxSettingsTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.local = os.path.join(self.root, sb.LOCAL)
        self.write(sb.SHIPPED, {"sandbox": {"enabled": True}})

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, rel, data):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data))

    def read_local(self):
        with open(self.local) as fh:
            return json.load(fh)

    def test_on_by_default_and_the_local_override_turns_it_off(self):
        self.assertTrue(sb.enabled(self.root))
        sb.set_enabled(self.root, False)
        self.assertEqual(self.read_local(), {"sandbox": {"enabled": False}})
        self.assertFalse(sb.enabled(self.root))
        sb.set_enabled(self.root, True)
        self.assertFalse(os.path.exists(self.local))
        self.assertTrue(sb.enabled(self.root))

    def test_other_local_keys_are_kept(self):
        mine = {"permissions": {"allow": ["Bash(make test)"]},
                "sandbox": {"autoAllowBashIfSandboxed": True}}
        self.write(sb.LOCAL, mine)
        sb.set_enabled(self.root, False)
        self.assertEqual(self.read_local()["permissions"], mine["permissions"])
        self.assertEqual(self.read_local()["sandbox"],
                         {"autoAllowBashIfSandboxed": True, "enabled": False})
        sb.set_enabled(self.root, True)
        self.assertEqual(self.read_local(), mine)

    def test_unreadable_local_settings_are_refused_and_left_alone(self):
        for bad in ("{not json", "[]", '{"sandbox": []}'):
            self.write(sb.LOCAL, bad)
            with self.assertRaises(sb.SandboxError):
                sb.set_enabled(self.root, False)
            with open(self.local) as fh:
                self.assertEqual(fh.read(), bad)

    def test_linux_needs_bwrap_and_socat(self):
        with mock.patch.object(sb.platform, "system", return_value="Linux"), \
                mock.patch.object(sb.shutil, "which", return_value=None):
            self.assertIn("bwrap and socat", sb.platform_problem())
        for code, expected in ((0, None), (1, "AppArmor")):
            probe = subprocess.CompletedProcess(
                [], code, "", "setting up uid map: Permission denied")
            with mock.patch.object(sb.platform, "system", return_value="Linux"), \
                    mock.patch.object(sb.shutil, "which", return_value="/usr/bin/x"), \
                    mock.patch.object(sb.subprocess, "run", return_value=probe):
                problem = sb.platform_problem()
            if expected is None:
                self.assertIsNone(problem)
            else:
                self.assertIn(expected, problem)
        with mock.patch.object(sb.platform, "system", return_value="Darwin"):
            self.assertIsNone(sb.platform_problem())

    def test_warnings_name_exclusions_and_commit_signing(self):
        hermetic = {"CLAUDE_CONFIG_DIR": self.root, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull}
        with mock.patch.dict(os.environ, hermetic):
            subprocess.run(["git", "init", "-q", self.root], check=True)
            self.assertEqual(sb.warnings(self.root), [])
            self.write(sb.LOCAL, {"sandbox": {"excludedCommands": ["docker *"]}})
            subprocess.run(["git", "config", "commit.gpgsign", "yes"],
                           cwd=self.root, check=True)
            found = sb.warnings(self.root)
        self.assertEqual(len(found), 2)
        self.assertIn("docker *", found[0])
        self.assertIn("commit.gpgsign false", found[1])


if __name__ == "__main__":
    unittest.main()
