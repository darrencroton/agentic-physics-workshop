"""The `gate` command line: status, brief, check, unlock, hint, skip,
allow-model, reset, plus any commands the exercise tool adds."""

import datetime
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

from . import answers, crypto, exercise, manifest as mf, packs, state as st
from . import tty

NOT_QUITE = "Not quite. Discuss and try again."
RECORDS_DIR = ".records"
USAGE = """usage: ./gate <command>

  status               level, persona, time on level, hints, allowed models
  brief                print the current level brief
  check                run this level's check: PASS or FAIL with a reason
  unlock               (humans) check, answer the gate, unlock the next level
  hint                 (humans) show the next hint tier that has unlocked
  skip --master        (humans) facilitator skip with the master passphrase
  allow-model <name>   (humans) facilitator model power-up
  reset                (humans) save records, then back to the start at level 0
"""


class GateError(Exception):
    """A user-facing gate failure."""


def _say(text=""):
    print(text)


def _load(root):
    manifest = mf.load_root_manifest(root)
    if not os.path.exists(st.state_path(root)):
        reset_workshop(root, manifest)
        _say("Initialised workshop state at level 0.")
    state = st.load_state(root)
    if state["exercise"] != manifest["exercise"]:
        raise GateError("state belongs to a different exercise; run ./gate reset")
    return manifest, state


def _tool(manifest):
    return exercise.load_tool(manifest)


def _level_dir(root, level):
    return os.path.join(root, st.STATE_DIR, "levels", str(level))


def _vault(root, name):
    return os.path.join(root, ".vault", name)


def _master_secret_from_prompt():
    passphrase = tty.ask_secret("Master passphrase: ")
    if not passphrase.strip():
        raise GateError("No passphrase given.")
    return crypto.master_secret(passphrase)


def _verify_master(root, secret):
    """The build writes .vault/master.check, openable only by the master slot."""
    path = _vault(root, "master.check")
    try:
        with open(path, "rb") as fh:
            packs.open_pack(fh.read(), [secret])
    except (OSError, crypto.PackError):
        return False
    return True


# ----------------------------------------------------------------- status

def cmd_status(root, args):
    manifest, state = _load(root)
    level = state["level"]
    entry = mf.level_by_id(manifest, level)
    record = st.level_record(state)
    _say("%s" % manifest["title"])
    _say("Level %d: %s%s" % (level, entry["title"],
                             "  (complete)" if state.get("complete") else ""))
    _say("Persona: %s" % state.get("persona", "?"))
    _say("Time on level: %d min (target %s)"
         % (int(st.minutes_on_level(state)),
            entry.get("target_minutes", "?")))
    _say("Hints used: %d of %d" % (len(record.get("hints_used", [])),
                                  len(_hints(root, level))))
    _say("Failed gate attempts: %d" % record.get("failed_attempts", 0))
    _say("Allowed models: %s" % ", ".join(state.get("allowed_models", [])))
    tool = _tool(manifest)
    lines = getattr(tool, "status_lines", None)
    if lines:
        for line in lines(root, state):
            _say(line)
    return 0


def cmd_brief(root, args):
    manifest, state = _load(root)
    level = state["level"]
    path = os.path.join(_level_dir(root, level), "BRIEF.md")
    if level == 0 and not os.path.exists(path):
        path = os.path.join(root, "README.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            sys.stdout.write(fh.read())
    except OSError:
        raise GateError("no brief found for level %d" % level)
    return 0


# ------------------------------------------------------------------ check

def _notes(stderr):
    """Return the 'Note: ' lines of a check's stderr."""
    return [line.strip() for line in (stderr or "").splitlines()
            if line.startswith("Note: ")]


def run_check(root, manifest, state):
    """Return (ok, reason, token, notes) for the current level's gate."""
    level = state["level"]
    entry = mf.level_by_id(manifest, level)
    gate = entry.get("gate", {"type": "none"})
    kind = gate.get("type", "none")
    if kind == "none":
        return True, "No check at this level.", None, []
    if kind == "verified":
        fn = exercise.resolve(_tool(manifest), "conditions", gate["condition"])
        ok, reason = fn(root, state, manifest)
        return ok, reason, None, []
    script = os.path.join(root, gate["check"])
    python = gate.get("python", "python3")
    if python == "venv":
        python = os.path.join(root, ".venv", "bin", "python")
    try:
        proc = subprocess.run([python, script], cwd=root, capture_output=True,
                              text=True, timeout=gate.get("timeout", 600))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "check could not run: %s" % exc, None, []
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        return False, " | ".join(tail), None, []
    token = crypto.canonical_token(proc.stdout)
    if crypto.verify_token(token) != gate.get("verify"):
        return False, gate.get("fail_message",
                               "the check ran but its output is not yet "
                               "correct"), None, []
    return (True, gate.get("pass_message", "check passed"), token,
            _notes(proc.stderr))


def cmd_check(root, args):
    manifest, state = _load(root)
    ok, reason, _, notes = run_check(root, manifest, state)
    _say("%s: %s" % ("PASS" if ok else "FAIL", reason))
    for note in notes if ok else []:
        _say(note)
    return 0 if ok else 1


# ------------------------------------------------------------------ hints

def _hints(root, level):
    data = None
    path = os.path.join(_level_dir(root, level), "hints.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    return data.get("tiers", []) if isinstance(data, dict) else []


def _hint_text(root, state, manifest, tier):
    """Return the tier's text, preferring the text_from function."""
    text = tier.get("text", "")
    name = tier.get("text_from")
    if name:
        try:
            fn = exercise.resolve(_tool(manifest), "hints", name)
            dynamic = fn(root, state, tier)
            if isinstance(dynamic, str) and dynamic.strip():
                text = dynamic
        except Exception:
            pass
    return text.strip()


def cmd_hint(root, args):
    tty.require_tty()
    manifest, state = _load(root)
    level = state["level"]
    tiers = _hints(root, level)
    record = st.level_record(state)
    used = record.setdefault("hints_used", [])
    minutes = st.minutes_on_level(state)
    for index, tier in enumerate(tiers):
        if index in used:
            continue
        wait = float(tier.get("unlock_after_minutes", 0))
        if minutes + 1e-9 < wait:
            _say("Hint %d of %d unlocks after %d minutes on this level "
                 "(you are at %d)." % (index + 1, len(tiers), wait,
                                       int(minutes)))
            return 1
        _say("Hint %d of %d:" % (index + 1, len(tiers)))
        text = _hint_text(root, state, manifest, tier)
        _say(text)
        used.append(index)
        st.save_state(root, state)
        st.append_log(root, "Hint %d used at level %d" % (index + 1, level),
                      text)
        return 0
    _say("No more hints at this level." if tiers else "No hints at this level.")
    return 1


# ----------------------------------------------------------------- unlock

def _questions(gate):
    return gate.get("questions", [])


def _talk_prompts(gate):
    """Return the gate's talk prompts as a list."""
    talk = gate.get("talk", [])
    return [talk] if isinstance(talk, str) else list(talk)


def _question_text(root, state, manifest, question):
    """Return (prompt, wrong_hint), preferring the text_from function."""
    prompt = question["prompt"]
    hint = question.get("wrong_hint", "")
    name = question.get("text_from")
    if name:
        try:
            fn = exercise.resolve(_tool(manifest), "questions", name)
            text = fn(root, state, question)
            if isinstance(text.get("prompt"), str) and text["prompt"]:
                prompt = text["prompt"]
            if isinstance(text.get("wrong_hint"), str) and text["wrong_hint"]:
                hint = text["wrong_hint"]
        except Exception:
            pass
    return prompt, hint


def _with_hints(message, hints):
    """Append a 'Hint:' line for each non-empty wrong-answer hint."""
    return "\n".join([message] + ["Hint: %s" % h for h in hints if h])


def _ask_graded_verified(root, state, manifest, gate):
    tool = _tool(manifest)
    for question in _questions(gate):
        prompt, hint = _question_text(root, state, manifest, question)
        answer = tty.ask(prompt.rstrip() + " ")
        validator = exercise.resolve(tool, "validators",
                                     question.get("validator", "gate.answer"))
        ok, reason = validator(root, state, question, answer)
        if not ok:
            st.log_failed_attempt(state, "verified")
            st.save_state(root, state)
            raise GateError(_with_hints(reason or NOT_QUITE, [hint]))
    return None


def _ask_graded_crypto(root, state, manifest, gate, token):
    """Return (slot secrets, hints of the questions asked).

    Each graded question can yield several candidate canonical forms (one per
    number typed); the secrets cover every combination of them.
    """
    forms = []
    hints = []
    for question in _questions(gate):
        prompt, hint = _question_text(root, state, manifest, question)
        hints.append(hint)
        answer = tty.ask(prompt.rstrip() + " ")
        try:
            candidates = answers.candidates(question, answer)
        except answers.AnswerError as exc:
            st.log_failed_attempt(state, "crypto-format")
            st.save_state(root, state)
            raise GateError(_with_hints("Please %s." % exc, hints))
        if candidates:
            forms.append(candidates)
    return [crypto.crypto_slot_secret(token, "|".join(combo))
            for combo in itertools.product(*forms)], hints


def _install_pack(root, manifest, state, secrets_list, new_level):
    """Decrypt level pack `new_level` and place its files."""
    path = _vault(root, "level%d.pack" % new_level)
    try:
        with open(path, "rb") as fh:
            pack_bytes = fh.read()
    except OSError:
        raise GateError("missing pack for level %d" % new_level)
    tmp = tempfile.mkdtemp(prefix="gate-unpack-")
    try:
        packs.unpack_to(pack_bytes, secrets_list, tmp)
        dest = _level_dir(root, new_level)
        os.makedirs(dest, exist_ok=True)
        entry = mf.level_by_id(manifest, new_level)
        files = dict(entry.get("files") or {})
        if "BRIEF.md" not in files and os.path.exists(
                os.path.join(tmp, "BRIEF.md")):
            files["BRIEF.md"] = "BRIEF.md"
        for name in os.listdir(tmp):
            src = os.path.join(tmp, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(dest, name))
        for pack_path, repo_path in files.items():
            src = os.path.join(tmp, pack_path)
            if not os.path.isfile(src):
                raise GateError("pack for level %d lacks %s"
                                % (new_level, pack_path))
            target = os.path.join(root, repo_path)
            os.makedirs(os.path.dirname(target) or root, exist_ok=True)
            shutil.copy2(src, target)
        return sorted(files.values())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _advance(root, manifest, state, secrets_list, how):
    """Install the next level's pack, advance state, run post-unlock."""
    level = state["level"]
    new_level = level + 1
    entry = mf.level_by_id(manifest, new_level)
    placed = _install_pack(root, manifest, state, secrets_list, new_level)
    st.advance_level(state, entry.get("persona", "coach"))
    st.save_state(root, state)
    _say("")
    minutes = entry.get("target_minutes")
    _header("Level %d unlocked: %s%s" % (
        new_level, entry["title"],
        " (about %s minutes)" % minutes if minutes else ""))
    shown = [name for name in placed if name != "BRIEF.md"]
    if shown:
        _say("New files: %s" % ", ".join(shown))
    st.append_log(root, "Level %d unlocked (%s)" % (new_level, how),
                  "Level %d: %s" % (new_level, entry["title"]))
    gate = mf.level_by_id(manifest, level).get("gate", {})
    post = gate.get("post_unlock")
    if post:
        fn = exercise.resolve(_tool(manifest), "post_unlock", post)
        try:
            message = fn(root, state, manifest, new_level)
        except Exception as exc:
            message = ("The post-unlock step failed (%s). Level %d is open; ask "
                       "a facilitator to check the repo." % (exc, new_level))
        if message:
            _say(message)
        st.save_state(root, state)
    start = entry.get("start")
    _say("Next: swap the Driver, then %s." % start if start
         else "Next: swap the Driver and read the brief.")
    _say("Brief: BRIEF.md (or ./gate brief)")


def _header(text):
    """Print a header line with a dash rule of the same length."""
    _say(text)
    _say("-" * len(text))


def _closing(gate):
    """Print the gate note, then the talk prompts (nothing to type)."""
    note = gate.get("note")
    if note:
        _say("")
        _say(note)
    prompts = _talk_prompts(gate)
    if prompts:
        _say("")
        _say("Talk it over (30 seconds, nothing to type):")
        for prompt in prompts:
            _say("  %s" % prompt.strip())


def cmd_unlock(root, args):
    tty.require_tty()
    manifest, state = _load(root)
    if state.get("complete"):
        _say("The exercise is complete. Well done.")
        return 0
    level = state["level"]
    entry = mf.level_by_id(manifest, level)
    gate = entry.get("gate", {"type": "none"})
    ok, reason, token, notes = run_check(root, manifest, state)
    _say("%s: %s" % ("PASS" if ok else "FAIL", reason))
    if not ok:
        st.log_failed_attempt(state, "check")
        st.save_state(root, state)
        return 1
    for note in notes:
        _say(note)
    kind = gate.get("type", "none")
    last = mf.is_last_level(manifest, level)
    hints = []
    if kind == "verified":
        _ask_graded_verified(root, state, manifest, gate)
        secrets_list = None
        if not last:
            tool = _tool(manifest)
            secrets_list = [tool.level_secret(root, level)]
    elif kind == "crypto":
        secrets_list, hints = _ask_graded_crypto(root, state, manifest, gate,
                                                 token)
    else:
        secrets_list = [b""]
    if last:
        state["complete"] = True
        st.level_record(state)["unlocked"] = st.now_iso()
        st.save_state(root, state)
        _say("")
        _header("Exercise complete. Well done.")
        st.append_log(root, "Exercise complete", entry["title"])
    else:
        try:
            _advance(root, manifest, state, secrets_list, "unlock")
        except crypto.PackError:
            st.log_failed_attempt(state, kind)
            st.save_state(root, state)
            raise GateError(_with_hints(NOT_QUITE, hints))
    _closing(gate)
    return 0


# ------------------------------------------------------------------- skip

def cmd_skip(root, args):
    tty.require_tty()
    if "--master" not in args:
        raise GateError("usage: ./gate skip --master")
    manifest, state = _load(root)
    if state.get("complete"):
        _say("The exercise is already complete.")
        return 0
    level = state["level"]
    secret = _master_secret_from_prompt()
    if not _verify_master(root, secret):
        st.log_failed_attempt(state, "master")
        st.save_state(root, state)
        raise GateError("That is not the master passphrase.")
    reason = tty.ask("Reason for the skip (logged): ")
    state.setdefault("skips", []).append(
        {"ts": st.now_iso(), "level": level, "reason": reason})
    if mf.is_last_level(manifest, level):
        state["complete"] = True
        st.save_state(root, state)
        _say("Final level marked complete by the facilitator.")
    else:
        _advance(root, manifest, state, [secret], "master skip")
    st.append_log(root, "Facilitator skip at level %d" % level, reason)
    return 0


def cmd_allow_model(root, args):
    tty.require_tty()
    if len(args) != 1:
        raise GateError("usage: ./gate allow-model <name>")
    name = args[0].strip().lower()
    manifest, state = _load(root)
    secret = _master_secret_from_prompt()
    if not _verify_master(root, secret):
        st.log_failed_attempt(state, "master")
        st.save_state(root, state)
        raise GateError("That is not the master passphrase.")
    allowed = state.setdefault("allowed_models", [])
    if name not in allowed:
        allowed.append(name)
    st.save_state(root, state)
    st.append_log(root, "Model power-up", "Allowed models: %s"
                  % ", ".join(allowed))
    _say("Allowed models: %s. Switch with /model in Claude Code."
         % ", ".join(allowed))
    return 0


# ------------------------------------------------------------------ reset

def reset_workshop(root, manifest=None):
    """Rebuild .workshop/ at level 0 from .gatekit/levels/0.

    Touches neither git nor .records/; `cmd_reset` does those.
    """
    manifest = manifest or mf.load_root_manifest(root)
    workshop = os.path.join(root, st.STATE_DIR)
    removed = []
    for entry in manifest["levels"][1:]:
        targets = set((entry.get("files") or {}).values()) | {"BRIEF.md"}
        for rel in sorted(targets):
            path = os.path.join(root, rel)
            if os.path.isfile(path):
                os.unlink(path)
                removed.append(rel)
    if removed:
        _say("Removed unlocked files: %s" % ", ".join(sorted(set(removed))))
    shutil.rmtree(workshop, ignore_errors=True)
    os.makedirs(os.path.join(workshop, "levels"), exist_ok=True)
    src = os.path.join(root, ".gatekit", "levels", "0")
    if os.path.isdir(src):
        shutil.copytree(src, _level_dir(root, 0))
    st.save_state(root, st.initial_state(manifest))
    tool = _tool(manifest)
    on_reset = getattr(tool, "on_reset", None)
    if on_reset:
        on_reset(root)


def _git(root, *args):
    """Run git in `root`; return stdout or raise GateError."""
    try:
        proc = subprocess.run(["git"] + list(args), cwd=root,
                              capture_output=True, text=True)
    except OSError as exc:
        raise GateError("cannot run git: %s" % exc)
    if proc.returncode != 0:
        raise GateError("git %s failed: %s"
                        % (" ".join(args), proc.stderr.strip()))
    return proc.stdout


def _check_resettable(root):
    """Raise GateError unless root is its own git repo with a start tag."""
    try:
        top = _git(root, "rev-parse", "--show-toplevel").strip()
    except GateError:
        raise GateError("this folder is not a git repo, so ./gate reset "
                        "cannot take it back to the start. Nothing changed.")
    if os.path.realpath(top) != os.path.realpath(root):
        raise GateError("this folder is inside another git repo (%s); "
                        "./gate reset only works on the workshop repo itself. "
                        "Nothing changed." % top)
    for ref, what in (("refs/tags/start", "the 'start' tag"),
                      ("refs/heads/main", "the 'main' branch")):
        try:
            _git(root, "rev-parse", "-q", "--verify", ref + "^{commit}")
        except GateError:
            raise GateError("%s is missing, so ./gate reset cannot take the "
                            "repo back to the start. Nothing changed." % what)


def _uncommitted_diff(root):
    """Return a binary diff of HEAD against the working tree, as bytes.

    Includes binary changes and untracked, non-ignored files. A temporary
    copy of the index is used, so the real index is untouched.
    """
    tmp = tempfile.mkdtemp(prefix="gate-index-")
    try:
        index = os.path.join(tmp, "index")
        real = _git(root, "rev-parse", "--git-path", "index").strip()
        real = os.path.join(root, real)
        if os.path.exists(real):
            shutil.copy2(real, index)
        env = dict(os.environ, GIT_INDEX_FILE=index)
        for args in (["add", "-A"],
                     ["diff", "--binary", "--cached", "HEAD"]):
            proc = subprocess.run(["git"] + args, cwd=root, env=env,
                                  capture_output=True)
            if proc.returncode != 0:
                raise GateError("git %s failed: %s" % (
                    " ".join(args),
                    proc.stderr.decode("utf-8", "replace").strip()))
        return proc.stdout
    except OSError as exc:
        raise GateError("cannot run git: %s" % exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


SAVED_STASH_PREFIX = "refs/saved-stash/"


def _bundle_work(root, path):
    """Bundle every ref, stash entries included, if there is work past start.

    Each stash entry gets a temporary ref so --all reaches it; the temporary
    refs are always removed again.
    """
    made = []
    try:
        for num, sha in enumerate(
                _git(root, "stash", "list", "--format=%H").split()):
            ref = "%s%d" % (SAVED_STASH_PREFIX, num)
            _git(root, "update-ref", ref, sha)
            made.append(ref)
        if _git(root, "rev-list", "--all", "^start").strip():
            _git(root, "bundle", "create", path, "--all")
    finally:
        for ref in made:
            subprocess.run(["git", "update-ref", "-d", ref], cwd=root,
                           capture_output=True)


def save_records(root, manifest):
    """Write .records/<stamp>/ and return its path.

    Also saves the commits beyond start as work.bundle and tracked changes
    as uncommitted.diff. Raises GateError on failure.
    """
    stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
    base = os.path.join(root, RECORDS_DIR)
    outdir = os.path.join(base, stamp)
    for n in itertools.count(2):
        if not os.path.exists(outdir):
            break
        outdir = os.path.join(base, "%s-%d" % (stamp, n))
    try:
        os.makedirs(outdir)
        if os.path.exists(st.state_path(root)):
            shutil.copy2(st.state_path(root),
                         os.path.join(outdir, st.STATE_FILE))
        _bundle_work(root, os.path.join(outdir, "work.bundle"))
        diff = _uncommitted_diff(root)
        if diff:
            with open(os.path.join(outdir, "uncommitted.diff"), "wb") as fh:
                fh.write(diff)
        log = _git(root, "log", "--oneline", "--all", "--decorate")
        with open(os.path.join(outdir, "git-log.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(log)
        for rel in manifest.get("records", []):
            src = os.path.join(root, rel)
            if os.path.isfile(src):
                dst = os.path.join(outdir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        hook = getattr(_tool(manifest), "on_records", None)
        if hook:
            hook(root, outdir)
    except Exception as exc:
        raise GateError("could not save the records (%s). Nothing was reset."
                        % exc)
    return outdir


def _git_reset_to_start(root):
    """Return the repo to the start tag, keeping .venv, .workshop, .records.

    Also removes the stash, any leftover saved-stash refs and every tag
    except start; the work is already in work.bundle.
    """
    _git(root, "checkout", "-q", "-f", "main")
    _git(root, "reset", "-q", "--hard", "start")
    _git(root, "clean", "-q", "-fdx", "-e", ".venv", "-e", ".workshop",
         "-e", "/" + RECORDS_DIR)
    for line in _git(root, "for-each-ref", "--format=%(refname:short)",
                     "refs/heads").split():
        if line != "main":
            _git(root, "branch", "-q", "-D", line)
    for tag in _git(root, "tag", "--list").split():
        if tag != "start":
            _git(root, "tag", "-d", tag)
    if _git(root, "for-each-ref", "refs/stash").strip():
        _git(root, "update-ref", "-d", "refs/stash")
    for ref in _git(root, "for-each-ref", "--format=%(refname)",
                    "refs/saved-stash").split():
        _git(root, "update-ref", "-d", ref)


RESET_NOTICE = """\
Your group's records are saved to .records/<date-time>/, then the repo goes
back to the start. Commits, changes, untracked files and other branches go;
.venv is kept."""


def cmd_reset(root, args):
    """(humans) save records, then back to the start at level 0."""
    tty.require_tty()
    manifest = mf.load_root_manifest(root)
    _check_resettable(root)
    if "--yes" not in args:
        _say(RESET_NOTICE)
        if not tty.confirm("Go back to level 0?"):
            _say("Nothing changed.")
            return 1
    outdir = save_records(root, manifest)
    _say("Records saved to %s" % os.path.relpath(outdir, root))
    try:
        _git_reset_to_start(root)
    except GateError as exc:
        raise GateError("%s\nThe records are safe in %s. Run ./gate reset "
                        "again to finish." % (exc, outdir))
    reset_workshop(root, manifest)
    _say("Back to level 0 at the start commit (.venv kept).")
    return 0


COMMANDS = {
    "status": cmd_status, "brief": cmd_brief, "check": cmd_check,
    "unlock": cmd_unlock, "hint": cmd_hint, "skip": cmd_skip,
    "allow-model": cmd_allow_model, "reset": cmd_reset,
}


def _tool_commands(root):
    """The exercise tool's gate_commands, or {} when there is none."""
    try:
        tool = _tool(mf.load_root_manifest(root))
    except (mf.ManifestError, exercise.ExerciseError):
        return {}
    return getattr(tool, "gate_commands", None) or {}


def _usage(root):
    lines = [USAGE]
    for name, fn in sorted(_tool_commands(root).items()):
        doc = (fn.__doc__ or "").strip().splitlines()
        lines.append("  %-20s %s\n" % (name, doc[0] if doc else ""))
    return "".join(lines)


def main(root, argv):
    """Entry point used by the `gate` launcher."""
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(_usage(root))
        return 0
    command, args = argv[0], argv[1:]
    fn = COMMANDS.get(command) or _tool_commands(root).get(command)
    if fn is None:
        sys.stderr.write("unknown command: %s\n" % command)
        sys.stderr.write(_usage(root))
        return 2
    try:
        return fn(root, args)
    except tty.NotATerminal as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    except (GateError, st.StateError, mf.ManifestError,
            exercise.ExerciseError) as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        return 130
