import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest import mock

from gatekit import cli, state as st, tty
from tests import fakerepo

MANIFEST = dict(fakerepo.MANIFEST, records=["LOG.md", "MISSING.md"])


def git(root, *args):
    proc = subprocess.run(["git", "-c", "commit.gpgsign=false",
                           "-c", "user.name=t", "-c", "user.email=t@t"]
                          + list(args), cwd=root, capture_output=True,
                          text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.root = fakerepo.make(manifest=MANIFEST)
        fakerepo.git_init(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)

    def reset(self):
        out = io.StringIO()
        with mock.patch.object(tty, "require_tty"), \
                contextlib.redirect_stdout(out):
            code = cli.cmd_reset(self.root, ["--yes"])
        return code, out.getvalue()

    def make_progress(self):
        write(self.root, "LOG.md", "# my log\n")
        git(self.root, "commit", "-qam", "group work")
        git(self.root, "branch", "attempt-1")
        write(self.root, "scratch.txt", "untracked")
        write(self.root, ".venv/marker", "keep")
        state = st.load_state(self.root)
        st.advance_level(state, "coach")
        st.save_state(self.root, state)


class ResetTests(GitFixture):
    def test_reset_saves_records_then_returns_to_start(self):
        self.make_progress()
        code, out = self.reset()
        self.assertEqual(code, 0, out)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"),
                         git(self.root, "rev-parse", "start"))
        self.assertEqual(git(self.root, "branch", "--format=%(refname:short)"),
                         "main")
        self.assertFalse(os.path.exists(os.path.join(self.root, "scratch.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.root, ".venv", "marker")))
        self.assertEqual(st.load_state(self.root)["level"], 0)
        base = os.path.join(self.root, ".records")
        (stamp,) = os.listdir(base)
        saved = os.path.join(base, stamp)
        self.assertEqual(sorted(os.listdir(saved)),
                         ["LOG.md", "git-log.txt", "state.json",
                          "uncommitted.diff", "work.bundle"])
        with open(os.path.join(saved, "LOG.md")) as fh:
            self.assertEqual(fh.read(), "# my log\n")
        with open(os.path.join(saved, "git-log.txt")) as fh:
            self.assertIn("group work", fh.read())
        self.assertIn("Back to level 0 at the start commit (.venv kept).", out)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def saved_dir(self):
        base = os.path.join(self.root, ".records")
        (stamp,) = os.listdir(base)
        return os.path.join(base, stamp)

    def test_commits_beyond_start_are_bundled(self):
        self.make_progress()
        self.reset()
        bundle = os.path.join(self.saved_dir(), "work.bundle")
        clone = os.path.join(tempfile.mkdtemp(), "clone")
        self.addCleanup(shutil.rmtree, os.path.dirname(clone))
        git(os.path.dirname(clone), "clone", "-q", bundle, clone)
        self.assertIn("group work", git(clone, "log", "--oneline"))

    def test_no_commits_no_bundle(self):
        self.reset()
        self.assertFalse(os.path.exists(
            os.path.join(self.saved_dir(), "work.bundle")))

    def test_uncommitted_tracked_edit_is_saved(self):
        write(self.root, "README.md", "edited\n")
        self.reset()
        self.assertTrue(os.path.exists(
            os.path.join(self.saved_dir(), "uncommitted.diff")))

    def test_diff_has_untracked_and_binary_files_and_keeps_index(self):
        write(self.root, "README.md", "edited\n")
        write(self.root, "new_file.py", "print(1)\n")
        with open(os.path.join(self.root, "blob.bin"), "wb") as fh:
            fh.write(b"\x00\x01\x02\xff" * 50)
        git(self.root, "add", "blob.bin")
        with open(os.path.join(self.root, "blob.bin"), "wb") as fh:
            fh.write(b"\x00\x09\x02\xff" * 50)
        before = git(self.root, "status", "--porcelain")
        outdir = cli.save_records(self.root, MANIFEST)
        self.assertEqual(git(self.root, "status", "--porcelain"), before)
        with open(os.path.join(outdir, "uncommitted.diff"), "rb") as fh:
            diff = fh.read().decode("utf-8", "replace")
        self.assertIn("new_file.py", diff)
        self.assertIn("blob.bin", diff)
        self.assertIn("GIT binary patch", diff)
        self.assertIn("README.md", diff)

    def test_reset_removes_stash_and_extra_tags_but_keeps_start(self):
        self.make_progress()
        write(self.root, "README.md", "stash me\n")
        git(self.root, "stash")
        git(self.root, "tag", "group-tag")
        git(self.root, "update-ref", "refs/saved-stash/9", "HEAD")
        self.reset()
        self.assertEqual(
            git(self.root, "for-each-ref", "refs/saved-stash"), "")
        self.assertEqual(git(self.root, "tag", "--list"), "start")
        self.assertEqual(git(self.root, "stash", "list"), "")

    def test_bundle_keeps_every_stash_entry_and_leaves_no_temp_refs(self):
        shas = []
        for text in ("one\n", "two\n"):
            write(self.root, "README.md", text)
            git(self.root, "stash")
            shas.append(git(self.root, "rev-parse", "stash@{0}"))
        self.reset()
        clone = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, clone, ignore_errors=True)
        dest = os.path.join(clone, "restored")
        git(clone, "clone", "-q", os.path.join(self.saved_dir(), "work.bundle"),
            dest)
        for sha in shas:
            self.assertEqual(git(dest, "cat-file", "-t", sha), "commit")
        self.assertEqual(
            git(self.root, "for-each-ref", "refs/saved-stash"), "")

    def test_git_failure_after_saving_points_to_the_records(self):
        self.make_progress()
        with mock.patch.object(cli, "_git_reset_to_start",
                               side_effect=cli.GateError("git boom")):
            with self.assertRaises(cli.GateError) as ctx:
                self.reset()
        self.assertIn("The records are safe in", str(ctx.exception))
        self.assertIn("Run ./gate reset again to finish.", str(ctx.exception))
        code, _ = self.reset()
        self.assertEqual(code, 0)

    def test_second_reset_keeps_earlier_records(self):
        self.make_progress()
        self.reset()
        self.make_progress()
        self.reset()
        self.assertEqual(len(os.listdir(os.path.join(self.root, ".records"))), 2)

    def test_missing_start_tag_refuses_and_changes_nothing(self):
        self.make_progress()
        git(self.root, "tag", "-d", "start")
        with self.assertRaises(cli.GateError) as ctx:
            self.reset()
        self.assertIn("'start' tag is missing", str(ctx.exception))
        self.assertTrue(os.path.exists(os.path.join(self.root, "scratch.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".records")))
        self.assertEqual(st.load_state(self.root)["level"], 1)
        self.assertIn("attempt-1", git(self.root, "branch"))

    def test_untouched_repo_still_saves_records(self):
        code, out = self.reset()
        self.assertEqual(code, 0, out)
        self.assertIn("Records saved to", out)
        self.assertEqual(len(os.listdir(os.path.join(self.root, ".records"))), 1)

    def test_failing_records_hook_aborts_before_git(self):
        self.make_progress()
        tool = types.SimpleNamespace(on_records=mock.Mock(side_effect=OSError("disk")))
        with mock.patch.object(cli, "_tool", return_value=tool):
            with self.assertRaises(cli.GateError):
                self.reset()
        self.assertTrue(os.path.exists(os.path.join(self.root, "scratch.txt")))
        self.assertNotEqual(git(self.root, "rev-parse", "HEAD"),
                            git(self.root, "rev-parse", "start"))

    def test_any_exception_in_records_hook_is_a_gate_error(self):
        tool = types.SimpleNamespace(
            on_records=mock.Mock(side_effect=KeyError("state")))
        with mock.patch.object(cli, "_tool", return_value=tool):
            with self.assertRaises(cli.GateError) as ctx:
                self.reset()
        self.assertIn("Nothing was reset.", str(ctx.exception))


class GateCommandTests(unittest.TestCase):
    def setUp(self):
        self.root = fakerepo.make()
        self.calls = []

        def hello(root, args):
            """Say hello (humans)."""
            self.calls.append((root, args))
            return 7
        self.tool = types.SimpleNamespace(gate_commands={"hello": hello})

    def tearDown(self):
        shutil.rmtree(self.root)

    def main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "_tool", return_value=self.tool), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return cli.main(self.root, argv), out.getvalue(), err.getvalue()

    def test_exercise_command_is_dispatched(self):
        code, _, _ = self.main(["hello", "x"])
        self.assertEqual(code, 7)
        self.assertEqual(self.calls, [(self.root, ["x"])])

    def test_help_lists_it_and_unknown_still_fails(self):
        _, out, _ = self.main(["help"])
        self.assertIn("hello", out)
        self.assertIn("Say hello (humans).", out)
        code, _, err = self.main(["nope"])
        self.assertEqual(code, 2)
        self.assertIn("unknown command: nope", err)


if __name__ == "__main__":
    unittest.main()
