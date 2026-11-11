"""Claude Code's OS sandbox for the agent's commands: on by default.

The shipped `.claude/settings.json` turns it on. `./preflight --no-sandbox`
writes `sandbox.enabled: false` into `.claude/settings.local.json`, which
Claude Code merges over the shipped file, and `./preflight --sandbox`
removes that override again. Every other key in the local file is kept,
because Claude Code saves "don't ask again" approvals there too.

Inside the sandbox the agent's commands, and everything they start, write
only in the project and the temp folder, cannot read the credential paths
the shipped deny rules name, and reach the network only through a site a
person approves.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile

LOCAL = os.path.join(".claude", "settings.local.json")
SHIPPED = os.path.join(".claude", "settings.json")
MIN_CLAUDE = (2, 1, 321)
MPL_REL = os.path.join(".venv", ".cache", "matplotlib")


class SandboxError(Exception):
    pass


def load(root, rel=LOCAL):
    """Return a settings file as a dict ({} when the file is missing)."""
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise SandboxError("cannot read %s (%s); fix or remove it" % (rel, exc))
    if not isinstance(data, dict):
        raise SandboxError("%s is not a JSON object; fix or remove it" % rel)
    return data


def _save(root, data):
    path = os.path.join(root, LOCAL)
    if not data:
        if os.path.exists(path):
            os.remove(path)
        return
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".settings-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def set_enabled(root, on):
    """Remove the local override (on) or write `enabled: false` (off)."""
    data = load(root)
    block = data.get("sandbox", {})
    if not isinstance(block, dict):
        raise SandboxError("%s: \"sandbox\" is not a JSON object; fix or "
                           "remove it" % LOCAL)
    block = dict(block)
    if on:
        block.pop("enabled", None)
    else:
        block["enabled"] = False
    if block:
        data["sandbox"] = block
    else:
        data.pop("sandbox", None)
    _save(root, data)


def enabled(root):
    """The effective `sandbox.enabled`: the local file wins over the shipped one."""
    for rel in (LOCAL, SHIPPED):
        block = load(root, rel).get("sandbox")
        if isinstance(block, dict) and isinstance(block.get("enabled"), bool):
            return block["enabled"]
    return False


def platform_problem():
    """None if Claude Code's sandbox can run here, else what is missing."""
    system = platform.system()
    if system == "Darwin":
        return None
    if system == "Linux":
        missing = [name for name in ("bwrap", "socat") if not shutil.which(name)]
        if missing:
            return ("Claude Code's sandbox needs %s on Linux: install "
                    "bubblewrap and socat (for example `sudo apt install "
                    "bubblewrap socat`)" % " and ".join(missing))
        try:
            proc = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--dev",
                                   "/dev", "--unshare-net", "true"],
                                  capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError) as exc:
            return "bwrap could not run (%s)" % exc
        if proc.returncode != 0:
            detail = (proc.stderr.strip().splitlines() or ["no message"])[-1]
            return ("bwrap cannot make a sandbox here (%s); on Ubuntu 23.10 "
                    "or newer, AppArmor blocks it unless allowed" % detail)
        return None
    return "Claude Code's sandbox runs on macOS, Linux and WSL2 only"


def warnings(root):
    """Settings and git config that weaken the sandbox or break inside it."""
    found = []
    excluded = []
    user = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR")
                        or os.path.expanduser("~/.claude"), "settings.json")
    for path in (user, os.path.join(root, SHIPPED), os.path.join(root, LOCAL)):
        try:
            block = load(os.path.dirname(path),
                         os.path.basename(path)).get("sandbox")
        except SandboxError:
            continue
        if isinstance(block, dict) and isinstance(block.get("excludedCommands"), list):
            excluded += [str(cmd) for cmd in block["excludedCommands"]]
    if excluded:
        found.append("these commands run outside the sandbox "
                     "(sandbox.excludedCommands): %s" % ", ".join(excluded))

    def git_config(*args):
        try:
            proc = subprocess.run(["git", "config"] + list(args), cwd=root,
                                  capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return ""
        return proc.stdout.strip()

    if git_config("--bool", "--get", "commit.gpgsign") == "true":
        found.append("git signs commits here, but the sandbox hides your "
                     "signing key, so the agent's commits fail: run `git "
                     "config commit.gpgsign false` (this repo only)")
    hooks = git_config("--get", "core.hooksPath")
    if hooks:
        found.append("git runs hooks from %s; a hook that writes outside "
                     "this folder fails in the agent's commits" % hooks)
    return found


def claude_version():
    """The `claude` CLI version as a tuple, or None if it cannot be found."""
    exe = shutil.which("claude")
    if not exe:
        return None
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True,
                              text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.match(r"\s*(\d+)\.(\d+)\.(\d+)", proc.stdout)
    if proc.returncode != 0 or not match:
        return None
    return tuple(int(part) for part in match.groups())


def warm_matplotlib(root, python):
    """Build matplotlib's font cache where the shipped MPLCONFIGDIR points.

    Inside the sandbox fontconfig cannot write its own cache and prints
    errors whenever matplotlib rebuilds the font cache; a cache built here,
    outside, is reused. Does nothing if matplotlib is not installed.
    """
    env = dict(os.environ, MPLCONFIGDIR=os.path.join(root, MPL_REL))
    code = ("try:\n    import matplotlib.font_manager\n"
            "except ImportError:\n    pass\n")
    try:
        subprocess.run([python, "-c", code], cwd=root, env=env,
                       capture_output=True, timeout=300)
    except (OSError, subprocess.SubprocessError):
        pass
