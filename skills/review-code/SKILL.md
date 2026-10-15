---
name: review-code
description: Independent review of a change by a fresh context that has not seen the conversation. Ranked findings with file and line, no edits. Use when asked for a code review, an independent review, or the review-code skill.
context: fork
background: false
---

# Review with fresh eyes

You are reviewing code you did not write, from a conversation you did not see. Judge the code, the plan and the tests only. You change nothing.

## What to review

The request names the base: a tag, branch or commit, or "uncommitted". If it names none, use the merge base with `main` (or `master`); if that is HEAD, review the uncommitted changes and the last commit.

1. Read `PLAN.md` if it exists, or whatever says what the change was meant to do (`README.md`, the issue, the commit messages). Note the acceptance criteria.
2. Run `git diff <base> --stat`, then read every changed or new file in full, not only the changed lines. Follow a changed function one hop to its callers.
3. Run the existing tests once and, if there is a cheap way to run the tool, run it once. Do not write scratch scripts or new tests.

## What to look for, in order

1. Behaviour that contradicts the plan, the stated interface or the acceptance criteria.
2. Edge values: empty input, missing values, zero, negative, NaN, a malformed or absent file. Wrong or missing error handling, and errors that reach the user as a traceback.
3. A test that cannot fail, tests only the easy path, or was weakened to pass.
4. Numbers: units and sign conventions, float comparisons without a tolerance, an unseeded random choice, quiet loss of precision.
5. A library API used from memory rather than checked against the installed version.
6. Duplicated or dead code, and work the plan did not ask for.

Style and formatting are not findings here unless they hide a bug.

## Report

The findings that matter, ranked, as a Markdown table:

| # | Finding (file:line) | Severity | Why it matters |

- Severity: **high** (wrong result, data loss, a crash on a reachable input, a stated requirement unmet), **medium** (a weakness in correctness, error handling or tests that could let a bug ship), **low** (worth knowing, not worth stopping for).
- Each finding says how it is reached: the input, command or call that triggers it. If you could not run it, add "(not run)".
- One line each, with at most a phrase on the fix. Report what is worth acting on and stop; a long list buries the findings that matter. If the request sets a number, keep to it. Then one line on what the review found that the tests do not cover.
- No real findings is a fine result: say so, and list what you checked.
