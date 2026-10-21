"""Facilitator commands for Explorer, run as `./gate <name>` by a human.

dataset: set the Dataset line of PLAN.md at Level 0.
install-solution: install the reference package from the encrypted vault.

Both need a real terminal (the agent's guard also refuses them). Stdlib only
and importable on Python 3.9.
"""

import os
import re
import shutil
import subprocess
import tempfile

from gatekit import crypto, packs, state as st, tty

DATASETS = ("pulsars", "dimuons")
DATASET_LINE = re.compile(r"^Dataset:.*$", re.M)
FIRST_COMMIT = ("explorer/__init__.py", "explorer/data.py")


def _error(message):
    from gatekit.cli import GateError
    return GateError(message)


def _git(root, *args, check=True):
    proc = subprocess.run(["git", "-c", "commit.gpgsign=false"] + list(args),
                          cwd=root, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    if check and proc.returncode != 0:
        raise _error("git %s failed: %s" % (args[0], proc.stderr.strip()[-200:]))
    return proc


def _state(root):
    try:
        return st.load_state(root)
    except st.StateError as exc:
        raise _error(str(exc))


def dataset(root, args):
    """pulsars|dimuons: choose the dataset in PLAN.md (Level 0, before it is committed)."""
    tty.require_tty()
    if len(args) != 1 or args[0] not in DATASETS:
        raise _error("usage: ./gate dataset pulsars|dimuons")
    if _state(root)["level"] != 0:
        raise _error("The dataset is fixed once the plan is committed: it can only "
                     "be changed at Level 0.")
    if _git(root, "rev-parse", "--verify", "-q", "start^{commit}", check=False).returncode:
        raise _error("The git tag 'start' is missing: ask a facilitator.")
    log = _git(root, "log", "--format=%h", "start..HEAD", "--", "PLAN.md").stdout
    if log.strip():
        raise _error("The dataset is fixed once the plan is committed: PLAN.md "
                     "has been committed since the start.")
    path = os.path.join(root, "PLAN.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise _error("cannot read PLAN.md: %s" % exc)
    line = "Dataset: data/%s.csv" % args[0]
    if len(DATASET_LINE.findall(text)) != 1:
        raise _error("PLAN.md must have exactly one Dataset: line (the Makefile "
                     "reads it).")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(DATASET_LINE.sub(line, text, count=1))
    print("PLAN.md now says: %s" % line)
    print("It is not committed yet: the group commits it with the plan.")
    return 0


def _open_solution(root, secret, destination):
    try:
        with open(os.path.join(root, ".vault", "master.check"), "rb") as fh:
            packs.open_pack(fh.read(), [secret])
    except (OSError, crypto.PackError):
        return False
    try:
        with open(os.path.join(root, ".vault", "scoring.pack"), "rb") as fh:
            packs.unpack_to(fh.read(), [secret], destination)
    except (OSError, crypto.PackError) as exc:
        raise _error("cannot open .vault/scoring.pack: %s" % exc)
    return True


def _copy_tree(src, dest_root, rel):
    """Copy the files under src/rel to dest_root/rel; return their relative paths."""
    copied = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(src, rel)):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".pyc"):
                continue
            path = os.path.relpath(os.path.join(dirpath, name), src)
            target = os.path.join(dest_root, path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy(os.path.join(src, path), target)
            copied.append(path.replace(os.sep, "/"))
    return copied


def _replace_dir(root, rel):
    """Remove the group's tracked files under rel, so none can clash."""
    _git(root, "rm", "-r", "-q", "--ignore-unmatch", "--", rel)
    shutil.rmtree(os.path.join(root, rel), ignore_errors=True)


def install_solution(root, args):
    """--master: install the reference explorer/ (and tests/ from Level 2) and commit it."""
    tty.require_tty()
    if args != ["--master"]:
        raise _error("usage: ./gate install-solution --master")
    state = _state(root)
    level = state["level"]
    if level < 1:
        raise _error("There is nothing to install at Level 0: unlock Level 1 first.")
    passphrase = tty.ask_secret("Master passphrase: ")
    if not passphrase.strip():
        raise _error("No passphrase given.")
    base = tempfile.mkdtemp(prefix="explorer-solution-")
    try:
        hidden = os.path.join(base, "hidden")
        if not _open_solution(root, crypto.master_secret(passphrase), hidden):
            st.log_failed_attempt(state, "master")
            st.save_state(root, state)
            raise _error("That is not the master passphrase.")
        src = os.path.join(hidden, "solution")
        if _git(root, "status", "--porcelain", "--", "explorer", "tests").stdout.strip():
            _git(root, "add", "-A", "--", "explorer", "tests")
            _git(root, "commit", "-q", "-m",
                 "Save the group's work in progress before the facilitator install")
        _replace_dir(root, "explorer")
        copied = _copy_tree(src, root, "explorer")
        if not copied:
            raise _error("the vault holds no reference solution: ask a facilitator")
        first = [p for p in copied if p in FIRST_COMMIT]
        _git(root, "add", "--", *first)
        _git(root, "commit", "-q", "--allow-empty", "-m",
             "Facilitator install: explorer data layer (reference solution)")
        tests = []
        if level >= 2:
            _replace_dir(root, "tests")
            tests = _copy_tree(src, root, "tests")
        copied += tests
        st.append_log(root, "Facilitator installed the reference solution",
                      "Level %d. Files: %s" % (level, ", ".join(copied)))
        _git(root, "add", "-A", "--", "explorer", "tests", "LOG.md")
        _git(root, "commit", "-q", "--allow-empty", "-m",
             "Facilitator install: explorer command line and page%s (reference "
             "solution)" % (", tests" if tests else ""))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("Installed the reference solution and committed it: %s" % ", ".join(copied))
    print("Run ./gate check, then carry on from here.")
    return 0
