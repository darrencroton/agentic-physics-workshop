#!/usr/bin/env python3
"""Assemble dist/<exercise>/ from gatekit/ and exercises/<exercise>/.

usage: tools/build.py <exercise> --master-passphrase-file <path> [--out DIR]
                      [--setup-python PATH] [--keep-venv]

Steps: wipe and recreate the output, copy level0/, templates, tools and the
skills the manifest lists, render CLAUDE.md, render settings.json (model and
the human-only deny rules from the manifest), make the launchers executable,
pack levels and hidden assets, write .workshop/, git init, commit "Workshop
start" and tag `start`.
"""

import argparse
import copy
import itertools
import json
import os
import re
import secrets
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TOP, "gatekit"))

from gatekit import answers, crypto, hooklib, packs, manifest as mf  # noqa: E402

LEVEL_PRIVATE = ("persona.txt", "hints.json", "guard.json")
DENY_PLACEHOLDER = "__HUMAN_ONLY_DENY__"
# Finder metadata that may reappear while the output is being wiped.
IGNORED_LEFTOVERS = (".DS_Store",)


def log(text):
    print("build: " + text)


def read_passphrase(path):
    path = os.path.expanduser(path)
    crypto.ensure_secure_file(path)
    with open(path, "r", encoding="utf-8") as fh:
        passphrase = fh.read().strip()
    if len(passphrase) < 8:
        raise SystemExit("master passphrase is too short")
    return passphrase


def copy_tree(src, dst):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                  ".DS_Store"))


def wipe_output(out, keep_venv):
    venv = os.path.join(out, ".venv")
    stash = None
    if keep_venv and os.path.isdir(venv):
        stash = out + ".venv-keep"
        shutil.rmtree(stash, ignore_errors=True)
        os.rename(venv, stash)
    try:
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out, exist_ok=True)
        left = sorted(set(os.listdir(out)) - set(IGNORED_LEFTOVERS))
        if left:
            raise SystemExit("could not wipe %s: %s remain" % (out, ", ".join(left)))
    finally:
        if stash:
            os.makedirs(out, exist_ok=True)
            os.rename(stash, venv)
            log("kept existing .venv")


def crypto_secrets(gate, level_answers, master):
    """Slots for a crypto gate: every accepted answer combination plus master."""
    token = bytes.fromhex(level_answers["token"])
    forms = [answers.accepted_forms(q) or [""] for q in gate.get("questions", [])]
    combos = itertools.product(*forms) if forms else [()]
    secrets_list = []
    for combo in combos:
        canon = "|".join(c for c in combo if c)
        secrets_list.append(crypto.crypto_slot_secret(token, canon))
    secrets_list.append(crypto.master_secret(master))
    return secrets_list


def shipped_manifest(manifest):
    """Copy of the manifest without the answer keys of crypto gates."""
    shipped = copy.deepcopy(manifest)
    for level in shipped["levels"]:
        gate = level.get("gate", {})
        if gate.get("type") in ("crypto", "crypto-reflection"):
            for question in gate.get("questions", []):
                for key in ("accept", "lo", "hi"):
                    question.pop(key, None)
    return shipped


def build(exercise, passphrase_file, out, setup_python, keep_venv,
          exercises_dir=None):
    src = os.path.join(exercises_dir or os.path.join(TOP, "exercises"), exercise)
    if not os.path.isdir(src):
        raise SystemExit("no such exercise: %s" % src)
    manifest = mf.load_manifest(os.path.join(src, "manifest.json"))
    master = read_passphrase(passphrase_file)
    templates = os.path.join(TOP, "gatekit", "templates")
    out = os.path.abspath(out or os.path.join(TOP, "dist", exercise))
    protected = [os.path.abspath(p) for p in (TOP, src, os.path.join(TOP, "gatekit"),
                                              os.path.join(TOP, "exercises"),
                                              os.path.join(TOP, "tools"), os.path.expanduser("~"))]
    for item in protected:
        if out == item or item.startswith(out + os.sep):
            raise SystemExit("refusing to wipe %s: it contains the build sources" % out)
    if (os.path.isdir(out) and not os.path.isdir(os.path.join(out, ".gatekit"))
            and sorted(set(os.listdir(out)) - set(IGNORED_LEFTOVERS)) not in ([], [".venv"])):
        raise SystemExit("refusing to wipe %s: it is not an earlier build output" % out)

    wipe_output(out, keep_venv)
    log("output %s" % out)

    copy_tree(os.path.join(src, "level0"), out)
    for name in os.listdir(templates):
        path = os.path.join(templates, name)
        if os.path.isdir(path):
            copy_tree(path, os.path.join(out, name))
        else:
            shutil.copy2(path, os.path.join(out, name))
    for name in manifest.get("skills", []):
        skill = os.path.join(TOP, "skills", name)
        if os.path.basename(name) != name or not os.path.isfile(os.path.join(skill, "SKILL.md")):
            raise SystemExit("manifest lists unknown skill %r: no skills/%s/SKILL.md" % (name, name))
        copy_tree(skill, os.path.join(out, ".claude", "skills", name))
    os.makedirs(os.path.join(out, ".gatekit"))
    copy_tree(os.path.join(TOP, "gatekit", "gatekit"),
              os.path.join(out, ".gatekit", "gatekit"))
    os.unlink(os.path.join(out, ".gatekit", "gatekit", "ptyhelper.py"))
    shutil.copy2(os.path.join(src, "manifest.json"),
                 os.path.join(out, ".gatekit", "manifest.json"))
    copy_tree(os.path.join(src, "levels", "0"),
              os.path.join(out, ".gatekit", "levels", "0"))

    workshop_src = os.path.join(src, "workshop")
    for name in os.listdir(workshop_src) if os.path.isdir(workshop_src) else []:
        path = os.path.join(workshop_src, name)
        if name == "CLAUDE.workshop.md":
            shutil.copy2(path, os.path.join(out, "CLAUDE.md"))
        elif name == "preflight_extra.py":
            shutil.copy2(path, os.path.join(out, ".gatekit", name))
        elif os.path.isdir(path) and name == manifest.get("tool"):
            copy_tree(path, os.path.join(out, ".gatekit", name))
        elif os.path.isdir(path):
            copy_tree(path, os.path.join(out, name))
        else:
            shutil.copy2(path, os.path.join(out, name))

    render(os.path.join(out, ".claude", "settings.json"),
           {"__MODEL__": manifest.get("models", {}).get("default", "haiku")})
    render_human_only_deny(os.path.join(out, ".claude", "settings.json"),
                           manifest)
    render(os.path.join(out, "preflight"),
           {"__SETUP_PYTHON__": setup_python or "python3"})
    launchers = ("gate", "preflight", "tdd", "race") + tuple(
        n for n in hooklib.human_only(manifest)
        if n not in ("gate", "preflight", "tdd", "race"))
    for name in launchers:
        path = os.path.join(out, name)
        if os.path.exists(path):
            os.chmod(path, 0o755)

    answers_path = os.path.join(src, "answers.json")
    level_answers = {}
    if os.path.exists(answers_path):
        with open(answers_path, "r", encoding="utf-8") as fh:
            level_answers = json.load(fh)

    vault = os.path.join(out, ".vault")
    os.makedirs(vault)
    level_secrets = {}
    levels = manifest["levels"]
    for level in levels:
        n = level["id"]
        if n == 0:
            continue
        level_dir = os.path.join(src, "levels", str(n))
        if not os.path.isdir(level_dir):
            raise SystemExit("missing level directory %s" % level_dir)
        for required in ("persona.txt", "guard.json"):
            if not os.path.exists(os.path.join(level_dir, required)):
                raise SystemExit("level %d lacks %s" % (n, required))
        previous = levels[n - 1].get("gate", {"type": "none"})
        kind = previous.get("type", "none")
        if kind == "verified":
            level_secrets[str(n - 1)] = secrets.token_hex(32)
            slots = [bytes.fromhex(level_secrets[str(n - 1)]),
                     crypto.master_secret(master)]
        elif kind in ("crypto", "crypto-reflection"):
            key = str(n - 1)
            if key not in level_answers:
                raise SystemExit("answers.json lacks level %s token" % key)
            slots = crypto_secrets(previous, level_answers[key], master)
            previous["verify"] = crypto.verify_token(
                bytes.fromhex(level_answers[key]["token"]))
        else:
            slots = [b"", crypto.master_secret(master)]
        pack = packs.pack_directory(level_dir, slots, exercise, n)
        with open(os.path.join(vault, "level%d.pack" % n), "wb") as fh:
            fh.write(pack)
        log("packed level %d (%d slots)" % (n, len(slots)))

    last_gate = levels[-1].get("gate", {"type": "none"})
    if last_gate.get("type", "none") in ("crypto", "crypto-reflection"):
        key = str(len(levels) - 1)
        if key not in level_answers:
            raise SystemExit("answers.json lacks level %s token" % key)
        graded = [q for q in last_gate.get("questions", [])
                  if q.get("kind", "free") != "free"]
        if graded:
            raise SystemExit("the last level's crypto gate cannot have graded questions "
                             "(there is no pack to check the answer against): use "
                             "free questions or a reflection")
        last_gate["verify"] = crypto.verify_token(
            bytes.fromhex(level_answers[key]["token"]))

    with open(os.path.join(vault, "master.check"), "wb") as fh:
        fh.write(packs.build_pack(b"master", [crypto.master_secret(master)],
                                  exercise, -1))

    hidden = os.path.join(src, "hidden")
    if os.path.isdir(hidden):
        scoring_secret = secrets.token_hex(32)
        pack = packs.pack_directory(hidden, [bytes.fromhex(scoring_secret),
                                             crypto.master_secret(master)],
                                    exercise, -2)
        with open(os.path.join(vault, "scoring.pack"), "wb") as fh:
            fh.write(pack)
        level_secrets["scoring"] = scoring_secret
        log("packed hidden assets")

    tool = manifest.get("tool")
    if tool and level_secrets:
        pepper = secrets.token_hex(16)
        tool_dir = os.path.join(out, ".gatekit", tool)
        with open(os.path.join(tool_dir, "_pepper.py"), "w") as fh:
            fh.write('PEPPER = "%s"\n' % pepper)
        key = crypto.obfuscation_key(exercise, pepper)
        with open(os.path.join(vault, "keys.bin"), "wb") as fh:
            fh.write(packs.seal_json(level_secrets, key))
        log("wrote keys.bin (%d secrets, obfuscated)" % len(level_secrets))

    with open(os.path.join(out, ".gatekit", "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(shipped_manifest(manifest), fh, indent=2, sort_keys=True)
        fh.write("\n")

    from gatekit import cli
    sys.path.insert(0, os.path.join(out, ".gatekit"))
    cli.reset_workshop(out, manifest)
    log("wrote .workshop/ at level 0")

    git(out, "init", "-q", "-b", "main")
    git(out, "add", "-A")
    git(out, "-c", "commit.gpgsign=false", "commit", "-q", "-m",
        "Workshop start")
    git(out, "tag", "-f", "start")
    log("git init, commit, tag start")
    return out


def render(path, replacements):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    for old, new in replacements.items():
        text = text.replace(old, new)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def deny_entries(manifest):
    """Bash deny rules for the manifest's human-only exercise commands."""
    try:
        spec = hooklib.human_only(manifest)
    except ValueError as exc:
        raise SystemExit("manifest: %s" % exc) from exc
    return ["Bash(./%s %s *)" % (launcher, sub)
            for launcher, subs in spec.items() for sub in subs]


def render_human_only_deny(path, manifest):
    """Replace the placeholder deny element in settings.json with the rules."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    pattern = re.compile(r'^([ \t]*)"%s",[ \t]*\n' % DENY_PLACEHOLDER,
                         re.MULTILINE)
    if len(pattern.findall(text)) != 1:
        raise SystemExit("settings.json template needs exactly one %s element"
                         % DENY_PLACEHOLDER)
    entries = deny_entries(manifest)

    def expand(match):
        return "".join("%s%s,\n" % (match.group(1), json.dumps(e))
                       for e in entries)

    text = pattern.sub(expand, text)
    if DENY_PLACEHOLDER in text:
        raise SystemExit("placeholder left in settings.json")
    try:
        json.loads(text)
    except ValueError as exc:
        raise SystemExit("rendered settings.json is invalid: %s" % exc) from exc
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def git(cwd, *args):
    proc = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True,
                          text=True)
    if proc.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exercise")
    parser.add_argument("--master-passphrase-file", required=True)
    parser.add_argument("--out")
    parser.add_argument("--setup-python", default="/opt/homebrew/bin/python3.13")
    parser.add_argument("--keep-venv", action="store_true",
                        help="preserve an existing dist/<name>/.venv")
    parser.add_argument("--exercises-dir", help="override exercises/ root")
    args = parser.parse_args(argv)
    out = build(args.exercise, args.master_passphrase_file, args.out,
                args.setup_python, args.keep_venv, args.exercises_dir)
    print("built %s" % out)


if __name__ == "__main__":
    main()
