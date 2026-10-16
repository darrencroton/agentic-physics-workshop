"""Shared helpers for the workshop hooks (guard, model lock, teacher context).

Hooks run under whatever python3 is on PATH, so this module is stdlib-only
and Python 3.9 compatible.  Every helper fails closed: when state, manifest
or input cannot be read, the caller denies the action.
"""

import collections
import fnmatch
import json
import os
import re
import sys

# Paths the agent may never read, list or write.
SECRET_DIRS = (".vault", ".workshop", ".tdd", ".claude", ".gatekit",
               ".tdd-tools", ".git")
# Paths the agent may read but never edit (launchers and build-controlled files).
FROZEN_FILES = ("gate", "tdd", "race", "preflight", "AGENTS.md", "CLAUDE.md",
                "OTHER-AGENTS.md", "README.md", "BRIEF.md", "CLIENT_SPEC.md",
                "Makefile", "pytest.ini", "requirements.txt", ".gitignore")
FROZEN_DIRS = ("data",)

PATH_TOOLS = {"Read": "file_path", "Edit": "file_path", "Write": "file_path",
              "MultiEdit": "file_path", "NotebookEdit": "notebook_path",
              "Glob": "path", "Grep": "path"}
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

HUMAN_GATE = r"\bgate\b[^|;&\n]*\b(unlock|hint|skip|reset|allow-model)\b"
# Human-only exercise-tool subcommands used when a manifest has no "human_only".
DEFAULT_HUMAN_ONLY = {"tdd": ["red", "green", "refactor", "done", "abort",
                              "score", "new-attempt"]}
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PACKAGE_MANAGERS = (r"\bpip3?\b", r"-m\s*pip\b", r"\bensurepip\b", r"\buvx?\b",
                    r"\bbrew\b", r"\bnpm\b", r"\bconda\b", r"\bpipx\b",
                    r"\bpoetry\b", r"\beasy_install\b")
# A bare shell or python reading code from a pipe (not `||`); tested on text
# outside quotes and heredocs.
PIPE_TO_INTERPRETER = (r"(?<!\|)\|(?!\|)\s*(?:[\w.-]*/)*(?:sh|bash|zsh|python3?)"
                       r"(?:[ \t]+-[A-Za-z]*)*[ \t]*(?:$|[;&|)\n])")
PTY_TRICKS = (r"\bpty\b", r"\bopenpty\b", r"(^|[;&|]\s*)script\s", r"(^|[;&|]\s*)expect\b",
              r"\bunbuffer\b", r"\bsocat\b", r"\bfaketty\b",
              r"\bCLAUDECODE\b", r"\benv\s+-[iu]\b", r"\bunset\s+CLAUDE")
GIT_READERS = (r"\bgit\b[^|;&\n]*\b(show|cat-file|archive|bundle|fast-export|"
               r"grep|ls-tree|rev-list|format-patch|diff-tree|worktree)\b",
               r"\bgit\b[^|;&\n]*\bdiff\b[^|;&\n]*--no-index",
               r"\bgit\b[^|;&\n]*\blog\b[^|;&\n]*\s(-p|--patch|-u|-U\d*|--full-diff)\b",
               r"\bgit\b[^|;&\n]*\bconfig\b[^|;&\n]*core\.hooksPath")
# git clean with -x or -X deletes ignored files (.workshop, .venv).
GIT_CLEAN_X = r"\bgit\b[^|;&\n]*\bclean\b[^|;&\n]*\s-[a-zA-Z]*[xX]"
DOT_GLOBS = (r"(^|[\s/=:,{(])\.[\w-]*[\[\*\?{]", r"\{[^}]*,\s*\.", r"\.\*/")
SECRET_RE = r"\.(vault|workshop|gatekit|claude|git|tdd(-tools)?)\b"
# Shell commands that can modify files; a redirect is handled separately.
WRITE_VERBS = (r"\btee\b",
               r"\bsed\b(?:\s+(?:-[a-zA-Z]+|'[^']*'|\"[^\"]*\"))*\s+"
               r"(-[a-zA-Z]*i[a-zA-Z]*|--in-place)", r"\bcp\b",
               r"\bmv\b", r"\brm\b", r"\btouch\b", r"\bchmod\b",
               r"\bln\b", r"\bpatch\b", r"\bgit\s+(checkout|restore|reset|"
               r"stash|revert|rebase|clean|apply|cherry-pick|merge)\b",
               r"\bpython3?\s+(-[A-Za-z]+\s+)*[\w./-]+\.py\b",
               r"\bnode(js)?\s+(-[A-Za-z-]+\s+)*[\w./-]+\.[cm]?js\b",
               r"\bperl\b", r"\bruby\b",
               r"\b[gmn]?awk\b[^'\n]*'[^']*?\bprint(f)?\b"
               r"(?:[^;}'\"(\n]|\"[^\"\n]*\"|\((?:[^()\n]|\([^()\n]*\))*\))*[>|]")
# File-writing APIs in interpreter code (python -c, heredocs, node -e).
PYTHON_WRITES = (r"\bopen\([^)]*['\"](?:[wax]|r\+)", r"\.write_(text|bytes)\(",
                 r"\bshutil\.",
                 r"\bos\.(remove|unlink|rename|replace|symlink|link|makedirs|mkdir)\b",
                 r"\.(touch|unlink|mkdir|rmdir)\(", r"\bPath\([^)]*\)\.rename\(")
NODE_WRITES = (r"\b(writeFile|writeFileSync|appendFile|appendFileSync|"
               r"createWriteStream|rmSync|rmdir|rmdirSync|unlink|unlinkSync|"
               r"rename|renameSync|copyFile|copyFileSync|mkdir|mkdirSync|symlink|"
               r"symlinkSync|truncate|truncateSync|writeSync)\b", r"\bfs(\.promises)?\.rm\(",
              r"\b(?:openSync|fs(?:\.promises)?\.open)\([^)]*['\"](?:[wa][+x]?|r\+)['\"]")
ALWAYS_DENY = (r"(^|[;&|(])\s*(\S*/)?ln\s",)


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


def human_only(manifest):
    """Launcher name -> subcommand list of human-only exercise commands.

    Uses the manifest's optional "human_only" field, else the tdd default.
    Raises ValueError when the field is malformed.
    """
    spec = manifest.get("human_only") if isinstance(manifest, dict) else None
    if spec is None:
        return {k: list(v) for k, v in DEFAULT_HUMAN_ONLY.items()}
    if not isinstance(spec, dict):
        raise ValueError("human_only must be an object")
    result = {}
    for launcher, subs in spec.items():
        if (not _NAME_RE.match(str(launcher)) or not isinstance(subs, list)
                or not all(isinstance(s, str) and _NAME_RE.match(s)
                           for s in subs)):
            raise ValueError("human_only entry %r is malformed" % (launcher,))
        result[launcher] = list(subs)
    return result


def human_only_patterns(spec):
    """(direct, indirect) regexes for human-only commands from `human_only()`."""
    direct = [r"\b%s\b[^|;&\n]*\b(%s)\b"
              % (re.escape(launcher), "|".join(re.escape(s) for s in subs))
              for launcher, subs in sorted(spec.items()) if subs]
    launchers = ["gate"] + sorted(spec)
    indirect = r"\b(%s)\b\s+\$" % "|".join(re.escape(n) for n in launchers)
    return direct, indirect


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


def _rel(root, candidate):
    if candidate == root:
        return "."
    if candidate.startswith(root + os.sep):
        return os.path.relpath(candidate, root).replace(os.sep, "/")
    return None


def relative_paths(root, path):
    """(lexical, resolved) repo-relative posix paths; None where outside."""
    if not path:
        return None, None
    expanded = os.path.expanduser(path)
    lexical = os.path.abspath(os.path.join(root, expanded))
    return _rel(root, lexical), _rel(root, os.path.realpath(lexical))


def relative_path(root, path):
    """`path` relative to root in posix form; None if it leaves the repo."""
    lexical, resolved = relative_paths(root, path)
    return lexical if lexical is not None else resolved


def in_dir(rel, directory):
    """True if rel is `directory` or inside it."""
    return rel == directory or rel.startswith(directory + "/")


def is_secret(rel):
    """True for paths the agent may never touch (case-insensitive)."""
    low = rel.lower()
    return any(in_dir(low, d.lower()) for d in SECRET_DIRS)


def is_frozen(rel, launchers=()):
    """True for build-controlled paths the agent may read but not edit.

    `launchers` are extra frozen file names, such as the manifest's
    human-only launchers.
    """
    low = rel.lower()
    if low in {f.lower() for f in tuple(FROZEN_FILES) + tuple(launchers)}:
        return True
    return any(in_dir(low, d.lower()) for d in FROZEN_DIRS)


def normalise_command(command):
    """Strip quotes and backslashes so split spellings match the regexes."""
    return re.sub(r"[\"'\\]", "", command)


_MSG_HEREDOC = re.compile(
    r"\bgit\s+commit\b[^|;&\n$`]*?(\s-[a-zA-Z]*m|\s--message(?:=|\s))\s*"
    r"\"\$\(\s*cat\s+<<(-?)\s*(?:'(\w+)'|\"(\w+)\"|\\(\w+))[ \t]*\n")


def _strip_heredoc_messages(text):
    """Replace `-m "$(cat <<'X' ... X)"` commit messages with ` -m MSG`.

    A quoted delimiter makes the body literal, so nothing in it runs.  Any
    other shape is left for the caller to inspect.
    """
    pos = 0
    while True:
        match = _MSG_HEREDOC.search(text, pos)
        if match is None:
            return text
        delim = match.group(3) or match.group(4) or match.group(5)
        try:
            _, end = _heredoc_end(text, match.end(), delim, bool(match.group(2)))
        except Unparsable:
            pos = match.end()
            continue
        tail = re.match(r"\s*\)\"", text[end:])
        if tail is None:
            pos = match.end()
            continue
        text = text[:match.start(1)] + " -m MSG" + text[end + tail.end():]
        pos = match.start(1)


_QUOTED = r"(?:\"[^\"]*\"|'[^']*')"
# A git commit and the arguments on its line, quoted messages included.
_COMMIT_RE = re.compile(
    r"\bgit[ \t]+commit\b(?:[ \t]+(?:-[a-zA-Z]*m[ \t]*" + _QUOTED
    + r"|--message(?:=|[ \t]+)" + _QUOTED + r"|-[a-zA-Z]+"
    + r"|--[\w-]+(?:=(?:[^\s\"'|;&]+|" + _QUOTED + r"))?|" + _QUOTED + r"|[^\s\"'|;&]+))*")
_MESSAGE_RE = re.compile(r"(\s-[a-zA-Z]*m|\s--message(=|\s))\s*" + _QUOTED)


def strip_noise(command):
    """Drop literal commit messages and fd redirections, which are not writes.

    A heredoc commit message is always dropped.  Otherwise, when the command
    contains any substitution syntax ($(, backtick, ${, <( ) nothing is
    stripped, so a path hidden in a message is inspected.
    """
    text = _strip_heredoc_messages(command)
    if not re.search(r"\$\(|`|\$\{|<\(", text):
        text = _COMMIT_RE.sub(
            lambda m: _MESSAGE_RE.sub(" -m MSG", m.group(0)), text)
    text = re.sub(r"\d*>&\d+", " ", text)
    text = re.sub(r">\s*/dev/null", " ", text)
    text = re.sub(r"python3?\s+-m\s+pytest\b", "pytest", text)
    return text


class Unparsable(ValueError):
    """The shell text is outside what `parse_shell` understands."""


# code: text minus heredoc bodies (shell verbs); text: code plus interpreter
# heredoc bodies (write APIs, path mentions); masked: whole command with quoted
# regex-only spellings neutralised; outside: text outside quotes and heredocs;
# redirects: target words; shell_bodies: heredoc bodies fed to a shell;
# node: node code present; wild_gt: a '>' that is not a parsed redirect;
# quoted: per character of code, True inside quotes or a comment.
Parsed = collections.namedtuple(
    "Parsed", "code text masked outside redirects shell_bodies node wild_gt quoted")

_SHELLS = ("sh", "bash", "zsh", "dash", "ksh", "eval", "source", ".")
_WRAPPERS = ("env", "sudo", "time", "command", "exec", "nohup", "then", "do",
             "else", "if", "while", "!", "{", "timeout", "nice", "caffeinate",
             "stdbuf")
_DATA_READERS = ("cat", "tee", "git")
_WORD_END = " \t\n;|&<>()"
# Regex-only spellings (a group, an escaped dot, a dot quantifier before a
# word or regex character); masked inside quotes, where they are not globs.
_REGEX_ONLY = re.compile(r"\((?:\.\*|\.\+)\??\)|\\\.|\.[*+]\??(?=[\w)|$\\(])"
                         r"|(?<=[^'\"/])\.[*+]\??(?=/)")
_SHELL_C = re.compile(r"(?:^|[\s;&|(/])(?:sh|bash|zsh|dash|ksh)(?:\s+--?[\w-]+)*?"
                      r"\s+-[A-Za-z]*c[A-Za-z]*(?=\s|$)")
_NUMBER = re.compile(r"\d+(\.\d+)?[smhd]?$")
_NODE_RE = re.compile(r"\bnode(js)?\b")


def _consumer(segment):
    """Kind of command that reads a heredoc: shell, python, node, perl, ruby,
    data (cat, tee, git) or other (treated as interpreter code)."""
    words = re.findall(r"""(?:[^\s'"\\]|\\.|'[^']*'|"[^"]*")+""", segment)
    for word in words:
        word = re.sub(r"[\"'\\]", "", word)
        if (re.match(r"\w+=", word) or word in _WRAPPERS or word.startswith("-")
                or _NUMBER.match(word)):
            continue
        name = os.path.basename(word)
        if name in _SHELLS:
            return "shell"
        if re.match(r"python[0-9.]*$", name):
            return "python"
        if name in ("node", "nodejs"):
            return "node"
        return "data" if name in _DATA_READERS else name
    return "data"


def _heredoc_end(text, start, delim, dash):
    """(body, index of the end of the terminator line) of a heredoc."""
    pos = start
    while pos < len(text):
        end = text.find("\n", pos)
        end = len(text) if end < 0 else end
        line = text[pos:end]
        if (line.lstrip("\t") if dash else line) == delim:
            return text[start:pos], end
        pos = end + 1
    raise Unparsable("unterminated heredoc")


def _heredoc_delimiter(text, start):
    """(delimiter, quoted, end) of the word after `<<` or `<<-`."""
    pos = start
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    chars, quoted = [], False
    while pos < len(text) and text[pos] not in _WORD_END:
        char = text[pos]
        if char in "'\"":
            close = text.find(char, pos + 1)
            if close < 0:
                raise Unparsable("unbalanced quote")
            chars.append(text[pos + 1:close])
            quoted, pos = True, close + 1
        elif char == "\\" and pos + 1 < len(text):
            chars.append(text[pos + 1])
            quoted, pos = True, pos + 2
        else:
            chars.append(char)
            pos += 1
    if not chars:
        raise Unparsable("empty heredoc delimiter")
    return "".join(chars), quoted, pos


def _redirect_word(text, start):
    """The unquoted target word after a '>' operator."""
    pos = start
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    if text.startswith("$(", pos) or text.startswith("`", pos):
        raise Unparsable("computed redirect target")
    chars = []
    while pos < len(text) and text[pos] not in _WORD_END:
        char = text[pos]
        if char in "'\"":
            close = text.find(char, pos + 1)
            if close < 0:
                raise Unparsable("unbalanced quote")
            chars.append(text[pos + 1:close])
            pos = close + 1
        elif char == "\\" and pos + 1 < len(text):
            chars.append(text[pos + 1])
            pos += 2
        else:
            chars.append(char)
            pos += 1
    word = "".join(chars)
    if not word or "$(" in word or "`" in word:
        raise Unparsable("unreadable redirect target")
    return word


def _scan(text):
    """Walk `text` once; return per-character flags and the parsed pieces.

    Flags: 0 shell text, 1 quoted or comment, 2 quoted-heredoc body.
    """
    n = len(text)
    flags = [0] * n
    redirects, shell_bodies, interp = [], [], []
    wild_gt = False
    pending = []
    cmd_start = 0
    quote = None
    escapes = False
    i = 0
    while i < n:
        char = text[i]
        if quote:
            flags[i] = 1
            if char == "\\" and escapes and i + 1 < n:
                flags[i + 1] = 1
                i += 2
                continue
            if char == quote:
                flags[i] = 0
                quote = None
            elif quote == '"' and (char == "`" or text.startswith("$(", i)):
                raise Unparsable("substitution inside double quotes")
            i += 1
            continue
        if char == "\\":
            i += 2
        elif char in "'\"" or text.startswith("$'", i):
            if char == "$":
                i += 1
            quote = text[i]
            escapes = quote == '"' or char == "$"
            i += 1
        elif char == "#" and (i == 0 or text[i - 1] in " \t\n;|&("):
            end = text.find("\n", i)
            end = n if end < 0 else end
            for k in range(i, end):
                flags[k] = 1
            i = end
        elif text.startswith("<<", i) and not text.startswith("<<<", i):
            dash = text.startswith("<<-", i)
            delim, quoted, end = _heredoc_delimiter(text, i + (3 if dash else 2))
            kind = _consumer(text[cmd_start:i]) if quoted else "data"
            pending.append((delim, quoted, dash, kind))
            i = end
        elif char == ">":
            if text.startswith(">(", i):
                i += 2
                continue
            j = i + 1
            while j < n and text[j] in ">|&!":
                j += 1
            redirects.append(_redirect_word(text, j))
            i = j
        elif char == "\n":
            i += 1
            for delim, quoted, dash, kind in pending:
                body, end = _heredoc_end(text, i, delim, dash)
                if not quoted:
                    wild_gt = wild_gt or ">" in body
                else:
                    for k in range(i, end):
                        flags[k] = 2
                    if kind == "shell":
                        shell_bodies.append(body)
                    elif kind != "data":
                        interp.append((kind, body))
                i = min(end + 1, n)
            pending = []
            cmd_start = i
        else:
            if char in ";|&(`":
                cmd_start = i + 1
            i += 1
    if quote or pending:
        raise Unparsable("unbalanced quote or heredoc")
    return flags, redirects, shell_bodies, interp, wild_gt


def _fallback(command):
    """Whole-text conservative view used when parsing fails."""
    return Parsed(command, command, command, command, (), (),
                  bool(_NODE_RE.search(command)), ">" in command,
                  (False,) * len(command))


def parse_shell(command):
    """Split a command into the views the guard analyses.

    Falls back to whole-text analysis (a '>' anywhere is a write) when the
    command has unbalanced quotes, an unterminated heredoc, a substitution
    inside double quotes, a computed redirect target or a shell run with -c.
    """
    try:
        flags, redirects, shell_bodies, interp, wild_gt = _scan(command)
    except Unparsable:
        return _fallback(command)
    code = "".join(c for c, f in zip(command, flags) if f != 2)
    quoted = tuple(f == 1 for f in flags if f != 2)
    text = "\n".join([code] + [body for _, body in interp])
    outside, in_quote = [], False
    for char, flag in zip(command, flags):
        if flag == 0:
            if char not in "\"'\\":
                outside.append(char)
            in_quote = False
        elif flag == 1 and not in_quote:
            outside.append("\0")
            in_quote = True
    if _SHELL_C.search("".join(outside)):
        return _fallback(command)
    masked = _REGEX_ONLY.sub(
        lambda m: "X" if flags[m.start()] else m.group(0), command)
    node = bool(_NODE_RE.search(code)) or any(k == "node" for k, _ in interp)
    return Parsed(code, text, masked, "".join(outside), tuple(redirects),
                  tuple(shell_bodies), node, wild_gt, quoted)


def glob_match(rel, pattern):
    """fnmatch where '**' also matches across '/' and a bare dir matches below."""
    if pattern.endswith("/**"):
        return in_dir(rel, pattern[:-3])
    regex = fnmatch.translate(pattern).replace(r"\*\*", ".*")
    return re.match(regex, rel) is not None


def any_match(rel, patterns):
    """True if rel matches any glob in patterns."""
    return any(glob_match(rel, p) for p in patterns or [])


def mentions_secret(command, masked=None):
    """True if a shell command names a secret or tool path, in any spelling.

    Dot-globs are tested on `masked` (quoted regex spellings neutralised) when
    given; secret names are always tested on the whole command.
    """
    text = normalise_command(command)
    if re.search(SECRET_RE, text, re.IGNORECASE):
        return True
    glob_text = text if masked is None else normalise_command(masked)
    return any(re.search(p, glob_text) for p in DOT_GLOBS)


def pattern_hit(rel, pattern):
    """True if repo-relative `rel` is under a frozen glob or its base directory."""
    base = pattern.split("*")[0].rstrip("/")
    return glob_match(rel, pattern) or bool(base and in_dir(rel.lower(), base.lower()))


def mentions_path(command, rel_or_pattern):
    """Best-effort: does the command text mention this path or glob root?"""
    base = rel_or_pattern.split("*")[0].rstrip("/")
    if not base:
        return False
    return re.search(r"(^|[\s/=;|&(:])(\./)?" + re.escape(base) + r"(?=/|\s|$|[;|&),\]}])",
                     normalise_command(command), re.IGNORECASE) is not None


def has_write_verb(parsed):
    """True if the parsed command contains something that can modify files.

    Redirects are not counted here: the caller checks their targets.
    """
    if parsed.wild_gt or any(re.search(p, parsed.code) for p in WRITE_VERBS):
        return True
    apis = PYTHON_WRITES + (NODE_WRITES if parsed.node else ())
    return any(re.search(p, parsed.text) for p in apis)


def compile_any(patterns):
    """Return a function testing whether a command matches any regex."""
    compiled = [re.compile(p) for p in patterns]

    def test(command):
        return any(c.search(command) for c in compiled)
    return test
