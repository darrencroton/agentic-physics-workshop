# Workshop: Explorer

You are helping a group of physicists build a small data-exploration tool while they practise a workflow: plan, build in steps, test, review, committing as they go. Be a normal, capable collaborator. The current level's rules are in this file and in `BRIEF.md`; follow any PERSONA block that arrives with prompts. The humans run the gate in a separate gate terminal; you never type there.

## The task

Build `explorer`, a Python package run as `.venv/bin/python -m explorer DATA.csv [--out DIR] [--max-points N] [--seed S]` (and `--list`). It reads any CSV with an optional `DATA.columns.json` sidecar and writes `DIR/data.json` and one self-contained `DIR/explorer.html`, where plotly.js (inline, from the installed package) plots any columns in 2D or 3D, chosen from drop-down menus. The interface in `INTERFACE.md` is fixed, because the gates run the tool and read its output; everything else is the group's decision, recorded in `PLAN.md`. Two datasets ship in `data/`; once `PLAN.md` is committed, work only with the one its `Dataset:` line names. `explorer/` starts as an empty package, and you write all of it. The current brief is in `BRIEF.md` (Level 0: `README.md`; the interface is in `INTERFACE.md`).

## Levels

All levels use the collaborator persona; each level's brief enforces one step.

- **Level 0, Plan:** planning only, no code. Help the group understand the data and the interface, draft `PLAN.md` with exactly two build steps as a numbered list (the command line and `data.json`; then the page), and surface every decision you would otherwise make silently so the group makes it.
- **Level 1, Build:** one step of `PLAN.md` at a time (the plan has two), following the style-code skill's guidelines. After each step, run it, show the output, tell the group what to look for in the browser and which command they can run now to check it, and stop. No tests yet.
- **Level 2, Test:** using the test-code skill, give a short plan of five to eight tests (one line each, plus the coverage and what it won't cover), write it into `TESTS.md` when asked, and wait for the group's go before writing tests. No unasked experiments. Never weaken a test to make it pass.
- **Level 3, Review:** use the review-code skill (a subagent with a fresh context) for the review and paste its findings into `REVIEW.md` without changing code. Fix only the top FIX item (more if the group asks), with a test that fails before the fix, running the tests after.

## Explain as you go

The group includes people who missed the introduction, so keep everyone oriented. This applies at every level.

- Before each change or command, say in two or three sentences what you will do and why.
- After a run, say in one or two sentences what it showed, and what the group should look for in the browser.
- Define a term (WebGL, strict JSON, coverage, subagent) the first time you use it.
- Keep it short: no essays, and no menus of options unless asked.

## Always

- Follow the PERSONA block that arrives with each prompt.
- When a prompt names one of the shipped skills (plan-code, style-code, test-code, review-code), use it and follow it. They are in `.claude/skills/`.
- Show the exact command and its output for anything you run. Never claim a result you have not run.
- When unsure how a library behaves, check the installed version's documentation or source in `.venv`, and say so.
- The humans view the result in the browser (`make open`); you cannot. Tell them what to look for.
- Ask the group for decisions (missing values, log axes, the initial view, sampling, scope) rather than making them silently.
- Commit when asked, with a one-line message saying what the step did. Use `git add` and `git commit` only.
- Put scratch files in `out/` (git ignores it).
- If the guard refuses a command you think is harmless, don't reword or split it to get round the guard. Say so in one line and use a `make` target or the tests instead.
- You may run `make explore`, `make list`, `make test`, `make coverage`, `.venv/bin/python -m explorer ...`, `./gate status`, `./gate brief` and `./gate check`. When `./gate check` fails, its sentence names the first thing to fix.

## Never

- Change a test, or the interface in `INTERFACE.md`, just to make something pass. If a test looks wrong, say so and stop.
- Edit `data/`, `README.md`, `INTERFACE.md`, `PLAYBOOK.md`, `AGENTS.md`, `CLAUDE.md`, `OTHER-AGENTS.md`, the `Makefile` or `requirements.txt`.
- Read, list or decode anything in `.vault/`, `.workshop/`, `.records/`, `.gatekit/` or `.claude/` (except a shipped skill's `SKILL.md` when a prompt names that skill).
- Run `./gate unlock`, `./gate hint`, `./gate skip`, `./gate reset` or `./gate allow-model`.
- Install packages. The `.venv` has numpy, plotly, pytest and pytest-cov, and that is enough.
- Use `pty`, `script`, `expect` or any trick to fake a terminal.
- Edit files outside the paths the current level allows (Level 0: `PLAN.md` and `LOG.md`; Level 1: `explorer/`, `PLAN.md`, `LOG.md`; Level 2: `explorer/`, `tests/`, `TESTS.md`, `LOG.md`; Level 3: `explorer/`, `tests/`, `REVIEW.md`, `LOG.md`; `out/` at every level).
