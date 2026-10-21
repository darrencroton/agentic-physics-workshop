# Explorer

Your group has a dataset and a question a table can't answer: **what does it look like?** In about 45 minutes the agent will build you a browser tool that plots any columns in 2D or 3D, colours the points by another column, and lets you rotate, zoom and hover. Nothing off the shelf does exactly this for your data.

You'll build it the way you'd want a careful student to: **plan it, build it in checked steps, test it, have it reviewed**, committing each step that works. Each stage is a gate. `PLAYBOOK.md` is that habit on one page, and the four skills in `.claude/skills/` (plan-code, style-code, test-code, review-code) are the same habit for the agent. Both are yours to take home.

## Your dataset

Your leader has set the `Dataset:` line of `PLAN.md`. Once `PLAN.md` is committed, that is the only dataset you use. Sources are in `data/README.md`; each CSV has a column file beside it with every column's unit, description and log-scale hint.

- **Pulsars** (`data/pulsars.csv`): 4,503 pulsars from the ATNF catalogue. Sky position, distance, Galactic `XX`, `YY`, `ZZ` (kpc), spin period `P0` and its derivative `P1`, and derived quantities. Many values are missing.
- **Dimuons** (`data/dimuons.csv`): 60,000 CMS muon pairs from 2010. Energy, momentum, `pt`, `eta`, `phi` and charge per muon, and the pair's invariant mass `M`. Nothing missing, no text columns.

## The tool

The tool's interface is fixed, because the gates run it and read its output: a command that reads any CSV and writes `explorer.html` and `data.json`, with the page's controls and the `data.json` format specified. It is all in [`INTERFACE.md`](INTERFACE.md), which the agent reads. Everything else is your decision, in `PLAN.md`.

## Roles

- **Driver:** types the prompts into the agent. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock. Asks "is it in the plan?"
- **Sceptic:** owns the acceptance criteria and the evidence. Nothing is committed until they've seen the command and its output, and, once the page exists, someone has looked at it.
- **Scribe:** keeps `LOG.md`: prompts that worked and failed, the "caught it" moment, the decisions the agent made for you.
- **Coach:** your leader. Asks questions, and steps in on tooling problems.

Hands off the code: humans read, look and decide. All code changes and commits go through the agent.

## Two windows and a browser

1. **Agent window (large):** Claude Code. Only the Driver types here.
2. **Gate terminal:** a separate terminal for the humans: `./gate`, `make open`, `make test`. The agent never types here.
3. **Browser:** `make open` shows the page. The agent can't see it; you can.

Not using Claude Code? Read `OTHER-AGENTS.md` first.

## Level 0: Plan (about 8 minutes)

No code yet. The agent starts in **plan mode** (it reads and proposes, but changes nothing; `Shift+Tab` cycles the modes). Agree a plan, write it down, commit it.

1. In the agent window, type:

   > "Read README.md, INTERFACE.md, data/README.md and the column file for our dataset. Say what the data contains, which columns have missing values and how many, and anything unclear. Then, using the plan-code skill, propose a plan: the goal, the decisions it depends on, the design, two build steps that each end in something we can run and look at, acceptance criteria we can check, and what's out of scope. Ask me about any decision you're unsure of. Don't write any code."

2. Read it. Argue about it. Change it. The four decisions in `PLAN.md` are the group's, not the agent's. The Sceptic owns the acceptance criteria (aim for three or more, each checkable by eye or by test). The Navigator cuts anything beyond the interface.
3. Approve the plan. Ask the agent to write it into `PLAN.md`, keeping the template's headings and the `Dataset:` line exactly as it is, then to commit it.
4. `./gate check` names the first thing still missing. When it passes, run `./gate unlock` in the gate terminal.

**Watch for**

- Two steps only. If there are more, ask the agent to merge them: the command line, `--list` and `data.json` first; then the page.
- Decisions made silently: dropping rows, clipping logs, which columns the page opens on. Each belongs in `PLAN.md`, decided by you.
- A plan bigger than the job (class hierarchies, config systems). It's a prototype.
- The agent asks something nobody knows: pick a reasonable answer, write it down, move on. If it tries to write code, the guard refuses, on purpose.

**The gate:** `PLAN.md` complete (the Dataset line, every section filled in, exactly two steps) and committed. Fewer than three acceptance criteria, or a blank decision, only earns a note. Then a talk prompt, with nothing to type.

## Commands

| Command | What it does |
|---|---|
| `make explore` | Builds the page into `out/` (once the agent has built the tool) |
| `make open` | Opens `out/explorer.html` in your browser |
| `make list` | Lists columns, units and missing counts (once the tool has `--list`) |
| `make test` / `make coverage` | Runs the tests / shows lines no test runs |
| `./gate check` | Names the first thing still missing at this level |
| `./gate unlock` | Checks your work and opens the next level |
| `./gate hint` | A hint, unlocking as the level goes on (gate terminal) |
| `./gate brief` | Shows this level's brief; `./gate status` shows where you are |
