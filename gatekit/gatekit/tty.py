"""Interactive-terminal helpers for human-only commands."""

import getpass
import os
import sys

HUMANS_ONLY = "This command is for humans, in the gate terminal."


class NotATerminal(Exception):
    """Raised when a human-only command runs without a real terminal."""


def is_interactive():
    """True when both stdin and stdout are terminals."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def require_tty():
    """Raise NotATerminal unless both stdin and stdout are terminals.

    Also refuses inside a Claude Code tool call (CLAUDECODE is set there),
    which stops the easy pty tricks; a determined script can still unset it.
    """
    if not is_interactive():
        raise NotATerminal(HUMANS_ONLY)
    if os.environ.get("CLAUDECODE"):
        raise NotATerminal(HUMANS_ONLY + " This shell was started by Claude "
                           "Code; open a fresh Terminal window for the gate.")


def ask(prompt):
    """Read a visible answer; returns the stripped text."""
    try:
        return input(prompt).strip()
    except EOFError:
        raise NotATerminal("input ended before an answer was given")


def ask_secret(prompt):
    """Read a passphrase without echo."""
    try:
        return getpass.getpass(prompt)
    except EOFError:
        raise NotATerminal("input ended before a passphrase was given")


def confirm(prompt):
    """Ask a yes/no question; True only for an explicit yes."""
    return ask(prompt + " [y/N] ").lower() in ("y", "yes")
