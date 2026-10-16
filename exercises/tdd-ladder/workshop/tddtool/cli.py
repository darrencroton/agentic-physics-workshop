"""The `tdd` command line."""

import sys

from gatekit import state as st, tty
from tddtool import common as C
from tddtool import phases, scoring

USAGE = """usage: ./tdd <command>

  status               level, phase, cycle count, last score
  test [pytest args]   run the test suite in .venv (the agent may use this)
  ladder               scores recorded so far, by level
  red "<behaviour>"    (humans) open a cycle: one behaviour, one test
  green                (humans) tests committed and failing for the right reason
  refactor             (humans) all green, tests frozen
  done                 (humans) close the cycle
  abort [reason]       (humans) close the open cycle without credit
  score                (humans) acceptance, mutants killed, false alarms
  new-attempt          (humans) save work on a branch, restore the stub
"""

HUMAN_ONLY = ("red", "green", "refactor", "done", "abort", "score", "new-attempt")


def cmd_status(root, args):
    import tddtool
    state = C.load_state(root)
    print("Level %d" % state.get("level", 0))
    for line in tddtool.status_lines(root, state):
        print(line)
    return 0


def cmd_test(root, args):
    code, record, _ = C.run_pytest(root, args)
    return code


COMMANDS = {
    "status": cmd_status, "test": cmd_test, "ladder": scoring.cmd_ladder,
    "red": phases.cmd_red, "green": phases.cmd_green,
    "refactor": phases.cmd_refactor, "done": phases.cmd_done,
    "abort": phases.cmd_abort,
    "score": scoring.cmd_score, "new-attempt": phases.cmd_new_attempt,
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
    except C.TddError as exc:
        sys.stderr.write("REFUSED: %s\n" % exc)
        return 1
    except st.StateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        return 130
