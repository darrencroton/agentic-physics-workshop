"""The `race` command line."""

import sys

from gatekit import state as st, tty
from racetool import common as C
from racetool import records, submit

USAGE = """usage: ./race <command>

  status                     level, division, last three bench runs, submissions
  log                        the bench log as a table (bad signatures flagged)
  board                      your submissions: score, division, time, commit
  submit                     (humans) score the committed entry on the hidden catalogue
  install-solution <level>   (facilitators) install a level's solution; needs the master passphrase

Bench runs are made with make: make bench N=2000 IMPL=fast, make check,
make profile, make fit.
"""

# TTY layer for the human-only commands; must match "human_only" in
# manifest.json (the guard and deny rules read the manifest).
HUMAN_ONLY = ("submit", "install-solution")


def cmd_status(root, args):
    import racetool
    state = C.load_state(root)
    print("Level %d" % state.get("level", 0))
    for line in racetool.status_lines(root, state):
        print(line)
    return 0


COMMANDS = {
    "status": cmd_status, "log": records.cmd_log, "board": records.cmd_board,
    "submit": submit.cmd_submit, "install-solution": submit.cmd_install_solution,
}


def main(root, argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(USAGE)
        return 0
    command, args = argv[0], argv[1:]
    fn = COMMANDS.get(command)
    if fn is None:
        sys.stderr.write("unknown command: %s\n" % command)
        sys.stderr.write(USAGE)
        return 2
    try:
        if command in HUMAN_ONLY:
            tty.require_tty()
        return fn(root, args)
    except tty.NotATerminal as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    except C.RaceError as exc:
        sys.stderr.write("REFUSED: %s\n" % exc)
        return 1
    except st.StateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        return 130
