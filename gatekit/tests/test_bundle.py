import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools")
spec = importlib.util.spec_from_file_location(
    "bundle_tool", os.path.join(TOOLS, "bundle.py"))
bundle_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle_tool)


def git(repo, *args):
    subprocess.run(["git", "-c", "commit.gpgsign=false",
                    "-c", "user.name=t", "-c", "user.email=t@t"] + list(args),
                   cwd=repo, check=True, capture_output=True)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dist = os.path.join(self.tmp, "dist")
        self.repo = os.path.join(self.dist, "ex")
        os.makedirs(os.path.join(self.repo, ".workshop"))
        with open(os.path.join(self.repo, ".workshop", "state.json"), "w") as fh:
            json.dump({"level": 0}, fh)
        with open(os.path.join(self.repo, ".gitignore"), "w") as fh:
            fh.write(".workshop/\n")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Workshop start")
        git(self.repo, "tag", "start")
        self.out = os.path.join(self.tmp, "ex.bundle")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_clean_tree_is_bundled_and_verified(self):
        path = bundle_tool.bundle("ex", self.out, self.dist)
        self.assertEqual(path, self.out)
        self.assertGreater(os.path.getsize(path), 0)

    def test_dirty_tree_is_refused(self):
        with open(os.path.join(self.repo, "stray.txt"), "w") as fh:
            fh.write("x")
        with self.assertRaisesRegex(bundle_tool.BundleError, "not clean"):
            bundle_tool.bundle("ex", self.out, self.dist)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
