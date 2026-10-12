"""Shared helpers for the workshop hooks (guard, model lock, teacher context).

Hooks run under whatever python3 is on PATH, so this module is stdlib-only
and Python 3.9 compatible.  Every helper fails closed: when state, manifest
or input cannot be read, the caller denies the action.
"""

import fnmatch
import json
import os
import re
import sys

# Paths Claude may never read, list or write.
SECRET_DIRS = (".vault", ".workshop", ".tdd", ".claude", ".gatekit",
               ".tdd-tools", ".git")
# Paths Claude may read but never edit (launchers and build-controlled files).
FROZEN_FILES = ("gate", "tdd", "preflight", "CLAUDE.md", "README.md",
                "BRIEF.md", "CLIENT_SPEC.md", "Makefile", "pytest.ini",
                "requirements.txt", ".gitignore")
FROZEN_DIRS = ("data",)

PATH_TOOLS = {"Read": "file_path", "Edit": "file_path", "Write": "file_path",
              "MultiEdit": "file_path", "NotebookEdit": "notebook_path",
              "Glob": "path", "Grep": "path"}
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

HUMAN_GATE = r"\bgate\b[^|;&\n]*\b(unlock|hint|skip|reset|allow-model)\b"
HUMAN_TDD = r"\btdd\b[^|;&\n]*\b(red|green|refactor|done|score|new-attempt)\b"
HUMAN_INDIRECT = r"\b(gate|tdd)\b\s+\$"
PACKAGE_MANAGERS = (r"\bpip3?\b", r"-m\s*pip\b", r"\bensurepip\b", r"\buvx?\b",
                    r"\bbrew\b", r"\bnpm\b", r"\bconda\b", r"\bpipx\b",
                    r"\bpoetry\b", r"\beasy_install\b",
                    r"\|\s*(sh|bash|zsh|python3?)\b")
PTY_TRICKS = (r"\bpty\b", r"\bopenpty\b", r"\bscript\s", r"\bexpect\b",
              r"\bunbuffer\b", r"\bsocat\b", r"\bfaketty\b",
              r"\bCLAUDECODE\b", r"\benv\s+-[iu]\b", r"\bunset\s+CLAUDE")
GIT_READERS = (r"\bgit\b[^|;&\n]*\b(show|cat-file|archive|bundle|fast-export|"
               r"grep|ls-tree|rev-list|format-patch|diff-tree|worktree)\b",
               r"\bgit\b[^|;&\n]*\blog\b[^|;&\n]*\s(-p|--patch|-u|--full-diff)\b",
               r"\bgit\b[^|;&\n]*\bconfig\b[^|;&\n]*core\.hooksPath")
DOT_GLOBS = (r"(^|[\s/=:,{(])\.[\w-]*[\[\*\?{]", r"\{[^}]*,\s*\.", r"\.\*/")
SECRET_RE = r"\.(vault|workshop|gatekit|claude|git|tdd(-tools)?)\b"
WRITE_VERBS = (r">{1,2}", r"\btee\b", r"\bsed\s+-[a-zA-Z]*i", r"\bcp\b",
               r"\bmv\b", r"\brm\b", r"\btouch\b", r"\bmkdir\b", r"\bchmod\b",
               r"\bln\b", r"\bpatch\b", r"\bgit\s+(checkout|restore|reset|"
               r"stash|revert|rebase|clean|apply|cherry-pick|merge)\b",
               r"\bpython3?\b", r"\bperl\b", r"\bruby\b", r"\bnode\b")


def project_dir():
    """The workshop repo root: CLAUDE_PROJECT_DIR or the current directory."""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.realpath(root)


def read_hook_input():
    """Parse the hook JSON from stdin; raise ValueError when malformed."""
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("empty hook input")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("hook input is not an object")
    return data


def deny(event, reason):
    """Print a deny decision for `event` and exit 0."""
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": event, "permissionDecision": "deny",
        "permissionDecisionReason": reason}}) + "\n")
    sys.stdout.flush()
    sys.exit(0)


def allow():
    """Exit 0 with no output: the normal permission flow continues."""
    sys.exit(0)


def load_json(path):
    """Load a JSON file or return None when absent or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_text(path):
    """Return a file's text or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def load_state(root):
    """state.json or None."""
    return load_json(os.path.join(root, ".workshop", "state.json"))


def load_manifest(root):
    """manifest.json or None."""
    return load_json(os.path.join(root, ".gatekit", "manifest.json"))


def level_dir(root, level):
    """Directory holding the unlocked files for `level`."""
    return os.path.join(root, ".workshop", "levels", str(level))


def load_guard(root, level):
    """The level's guard.json or None."""
    return load_json(os.path.join(level_dir(root, level), "guard.json"))


def read_phase(root):
    """The TDD phase (none|red|green|refactor) or 'none'."""
    text = read_text(os.path.join(root, ".tdd", "phase"))
    phase = (text or "none").strip().lower()
    return phase if phase in ("none", "red", "green", "refactor") else "none"


def relative_path(root, path):
    """`path` relative to root in posix form; None if it leaves the repo."""
    if not path:
        return None
    expanded = os.path.expanduser(path)
    lexical = os.path.abspath(os.path.join(root, expanded))
    full = os.path.realpath(lexical)
    for candidate in (lexical, full):
        if candidate == root:
            return "."
        if candidate.startswith(root + os.sep):
            return os.path.relpath(candidate, root).replace(os.sep, "/")
    return None


def in_dir(rel, directory):
    """True if rel is `directory` or inside it."""
    return rel == directory or rel.startswith(directory + "/")


def is_secret(rel):
    """True for paths Claude may never touch (case-insensitive)."""
    low = rel.lower()
    return any(in_dir(low, d.lower()) for d in SECRET_DIRS)


def is_frozen(rel):
    """True for build-controlled paths Claude may read but not edit."""
    low = rel.lower()
    if low in {f.lower() for f in FROZEN_FILES}:
        return True
    return any(in_dir(low, d.lower()) for d in FROZEN_DIRS)


def normalise_command(command):
    """Strip quotes and backslashes so split spellings match the regexes."""
    return re.sub(r"[\"'\\]", "", command)


def glob_match(rel, pattern):
    """fnmatch where '**' also matches across '/' and a bare dir matches below."""
    if pattern.endswith("/**"):
        return in_dir(rel, pattern[:-3])
    regex = fnmatch.translate(pattern).replace(r"\*\*", ".*")
    return re.match(regex, rel) is not None


def any_match(rel, patterns):
    """True if rel matches any glob in patterns."""
    return any(glob_match(rel, p) for p in patterns or [])


def mentions_secret(command):
    """True if a shell command names a secret or tool path, in any spelling."""
    text = normalise_command(command)
    if re.search(SECRET_RE, text, re.IGNORECASE):
        return True
    return any(re.search(p, text) for p in DOT_GLOBS)


def mentions_path(command, rel_or_pattern):
    """Best-effort: does the command text mention this path or glob root?"""
    base = rel_or_pattern.split("*")[0].rstrip("/")
    if not base:
        return False
    return re.search(r"(^|[\s/=;|&(:])" + re.escape(base) + r"(/|\b)",
                     normalise_command(command), re.IGNORECASE) is not None


def has_write_verb(command):
    """True if the command contains something that can modify files."""
    return any(re.search(p, command) for p in WRITE_VERBS)


def compile_any(patterns):
    """Return a function testing whether a command matches any regex."""
    compiled = [re.compile(p) for p in patterns]

    def test(command):
        return any(c.search(command) for c in compiled)
    return test
