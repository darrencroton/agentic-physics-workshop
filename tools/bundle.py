#!/usr/bin/env python3
"""Bundle a built exercise repo into one file to hand to a group.

usage: tools/bundle.py <exercise> [--out PATH]

Refuses unless dist/<exercise> is exactly as built: clean tree, one commit,
only the main branch, the start tag at HEAD and the state at level 0. Then
runs `git bundle create --all` and `git bundle verify`. The default output
is <exercise>.bundle in the current directory.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)


class BundleError(Exception):
    """The repo is not fit to bundle; the message names the fix."""


def git(repo, *args):
    """Run git in `repo`; return stdout or raise BundleError."""
    proc = subprocess.run(["git"] + list(args), cwd=repo,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise BundleError("git %s failed: %s" % (" ".join(args),
                                                 proc.stderr.strip()))
    return proc.stdout.strip()


def level_of(repo):
    """The level in .workshop/state.json; 0 when the file is absent.

    The state is not in the bundle, so an absent file counts as level 0.
    An unreadable file raises BundleError.
    """
    path = os.path.join(repo, ".workshop", "state.json")
    if not os.path.exists(path):
        return 0
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)["level"]
    except (OSError, ValueError, KeyError) as exc:
        raise BundleError("cannot read %s: %s" % (path, exc))


def check(repo, exercise):
    """Raise BundleError unless `repo` is a pristine build."""
    rebuild = "run: python3 tools/build.py %s" % exercise
    if not os.path.isdir(os.path.join(repo, ".git")):
        raise BundleError("%s is not a built repo; %s" % (repo, rebuild))
    if git(repo, "status", "--porcelain"):
        raise BundleError("the tree is not clean; run ./gate reset in %s, or "
                          "%s" % (repo, rebuild))
    if len(git(repo, "rev-list", "--all").split()) != 1:
        raise BundleError("there is not exactly one commit; run ./gate reset "
                          "in %s, or %s" % (repo, rebuild))
    branches = git(repo, "for-each-ref", "--format=%(refname:short)",
                   "refs/heads").split()
    if branches != ["main"]:
        raise BundleError("the branches are %s, not only main; run ./gate "
                          "reset in %s, or %s"
                          % (", ".join(branches) or "none", repo, rebuild))
    try:
        start = git(repo, "rev-parse", "-q", "--verify",
                    "refs/tags/start^{commit}")
    except BundleError:
        raise BundleError("the start tag is missing; %s" % rebuild)
    if start != git(repo, "rev-parse", "HEAD"):
        raise BundleError("the start tag is not at HEAD; run ./gate reset "
                          "in %s, or %s" % (repo, rebuild))
    if level_of(repo) != 0:
        raise BundleError("the state is not at level 0; run ./gate reset in "
                          "%s, or %s" % (repo, rebuild))


def bundle(exercise, out, dist=None):
    """Check dist/<exercise> and write the bundle; return its path."""
    repo = os.path.join(dist or os.path.join(TOP, "dist"), exercise)
    if not os.path.isdir(repo):
        raise BundleError("no such built exercise: %s; run: python3 "
                          "tools/build.py %s" % (repo, exercise))
    check(repo, exercise)
    out = os.path.abspath(out or "%s.bundle" % exercise)
    git(repo, "bundle", "create", out, "--all")
    git(repo, "bundle", "verify", out)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exercise")
    parser.add_argument("--out", help="default: ./<exercise>.bundle")
    parser.add_argument("--dist", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        path = bundle(args.exercise, args.out, args.dist)
    except BundleError as exc:
        sys.stderr.write("bundle: %s\n" % exc)
        return 1
    print("bundle: %s (%.1f MB)" % (path, os.path.getsize(path) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
