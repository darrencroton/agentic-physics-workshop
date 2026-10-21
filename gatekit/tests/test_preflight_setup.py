import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "preflight")
SETUP_LINE = "Setting up .venv"


def find_python311():
    """Return an interpreter that is Python 3.11+, or None."""
    if sys.version_info >= (3, 11):
        return sys.executable
    for name in ("python3.13", "python3.12", "python3.11"):
        path = shutil.which(name)
        if path:
            return path
    return None


@unittest.skipIf(find_python311() is None, "needs a Python 3.11+ to build .venv")
class PreflightSetupTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        with open(TEMPLATE, encoding="utf-8") as fh:
            text = fh.read().replace("__SETUP_PYTHON__", find_python311())
        self.script = os.path.join(self.root, "preflight")
        with open(self.script, "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(os.path.join(self.root, "requirements.txt"), "w") as fh:
            fh.write("# no packages: nothing to download\n")

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_preflight(self):
        return subprocess.run([sys.executable, self.script], cwd=self.root,
                              capture_output=True, text=True)

    def test_sets_up_venv_once_without_network(self):
        first = self.run_preflight()
        self.assertIn(SETUP_LINE, first.stdout, first.stdout + first.stderr)
        self.assertTrue(os.path.exists(
            os.path.join(self.root, ".venv", "bin", "python")))
        self.assertNotIn(".venv set-up", first.stdout)
        second = self.run_preflight()
        self.assertNotIn(SETUP_LINE, second.stdout)
        self.assertIn("[ok  ] .venv present", second.stdout)

    def test_no_requirements_creates_no_venv(self):
        os.remove(os.path.join(self.root, "requirements.txt"))
        proc = self.run_preflight()
        self.assertNotIn(SETUP_LINE, proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".venv")))


if __name__ == "__main__":
    unittest.main()
