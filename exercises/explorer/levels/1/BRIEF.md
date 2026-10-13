# Level 1: Build the prototype

**Target time:** 18 minutes. **Persona in force:** `collaborator`.

## Where we are

`PLAN.md` is committed: your goal, your four decisions, the steps and the acceptance criteria. Now build it, one step of the plan at a time, looking at the result yourselves and committing each step that works. Small steps make mistakes local: when something breaks, you know which step did it.

`explorer/` is open for editing. `tests/` stays frozen: testing is the next level.

## What to do

1. Make sure Claude is out of plan mode (`Shift+Tab` cycles the modes; the line under the prompt shows which is on). Then the playbook's *Build in small steps*:

   > "Implement step 1 of PLAN.md only. Run it and show me the exact command and output."

2. Look at the result yourselves: `make list`, or `make explore` and then `make open` in the gate terminal. If it works, ask Claude to commit it. Then: "Next step."
3. If Claude starts on more than one step, the Driver presses `Esc` and asks for one.
4. Run `./gate check` early and often. It names the first thing that is missing; paste that line to Claude.
5. If Claude seems unsure of a plotly detail, the *Evidence* prompt: "check the installed version's documentation".
6. When `./gate check` passes, play with the page for two minutes: rotate, zoom, hover, switch columns, palettes and log axes. Each of you names one feature you'd add. The Scribe writes them in `LOG.md`. Don't build them now.

## What to watch for

- "This should work now" with no command and output. The Sceptic asks for them.
- A plotly detail recalled wrongly: the hover text, the colour-bar title, the 3D trace.
- `./gate check` saying `data.json` is not valid JSON. That's a real bug, and one Python makes easy. Paste the sentence to Claude.
- Hover showing another row's values after sampling, or a colour bar with no unit. Only someone looking at the browser catches these.
- Level 3 runs the tool on **both** datasets. `make explore DATA=data/dimuons.csv` (or `data/pulsars.csv`) now saves a surprise later.

## Opening the gate

`./gate check` runs your tool four times on the `PLAN.md` dataset: with the defaults, with `--max-points 500`, with `--list`, and on a file that does not exist. It checks `data.json` and the page's controls against the README, and needs at least **3 commits** since Level 0 with nothing uncommitted under `explorer/` or in `PLAN.md`.

The question needs a human who has looked at the page. **Pulsars:** plot `XX`, `YY`, `ZZ` and rotate it; the known pulsars crowd around one point. What is there? **Dimuons:** plot `M` against `pt1` with log axes; which particle makes the sharp band near 3.1 GeV?

The reflection (logged): each of you, one feature you would add, and which the group liked best.

When the check passes and you've all looked at the page: commit, then `./gate unlock`.
