# Explorer

Your group has a dataset and a question a table can't answer: **what does it look like?** In about 45 minutes the agent will build you a browser tool that plots any columns in 2D or 3D, colours the points by another column, and lets you rotate, zoom and hover. Nothing off the shelf does exactly this for your data.

You'll build it the way you'd want a careful student to: **plan it, build it in checked steps, test it, have it reviewed**, committing each step that works.

## How it runs

| Level | | Target |
|---|---|---|
| 0 | Plan | 8 minutes |
| 1 | Build the prototype | 18 minutes |
| 2 | Test | 8 minutes |
| 3 | Review | 8 minutes |

A gate checks each level before the next one opens. **`BRIEF.md` is your running sheet**: what to do now, what to watch for, and what the gate needs. It changes at every unlock. Read this page once, then open `BRIEF.md` (or run `./gate brief`).

## Your dataset

Your leader sets the `Dataset:` line of `PLAN.md`. Once `PLAN.md` is committed, that is the only dataset you use. Each CSV has a column file beside it with every column's unit, description and log-scale hint.

- **Pulsars** (`data/pulsars.csv`): 4,503 pulsars from the ATNF catalogue. Sky position, distance, Galactic `XX`, `YY`, `ZZ` (kpc), spin period `P0` and its derivative `P1`, and derived quantities. Many values are missing.
- **Dimuons** (`data/dimuons.csv`): 60,000 CMS muon pairs from 2010. Energy, momentum, `pt`, `eta`, `phi` and charge per muon, and the pair's invariant mass `M`. Nothing missing, no text columns.

## Roles

- **Driver:** types the prompts into the agent. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock. Asks "is it in the plan?"
- **Sceptic:** owns the acceptance criteria and the evidence. Nothing is committed until they've seen the command and its output, and, once the page exists, someone has looked at it.
- **Scribe:** keeps `LOG.md`: prompts that worked and failed, the "caught it" moment, the decisions the agent made for you.

Your leader takes a role too, and looks after the laptop and the gate terminal.

Hands off the code: humans read, look and decide. All code changes and commits go through the agent.

## Two windows and a browser

1. **Agent window (large):** your agent (Claude Code, or another tool). Only the Driver types here.
2. **Gate terminal:** a separate terminal for the humans: `./gate`, `make open`, `make test`. The agent never types here.
3. **Browser:** `make open` shows the page. The agent can't see it; you can.

Not using Claude Code? Read `OTHER-AGENTS.md` first.

## Your files

| File | What it's for |
|---|---|
| `BRIEF.md` | What to do at this level |
| `PLAN.md`, `LOG.md` | Your plan and the Scribe's log. `TESTS.md` and `REVIEW.md` join them at Levels 2 and 3. |
| `INTERFACE.md` | The tool's fixed interface. The gates run the tool and read its output, so the agent must follow it. |
| `data/` | The two datasets, their column files, and `data/README.md` (sources and citations) |
| `PLAYBOOK.md` | The workflow on one page. The four skills in `.claude/skills/` (plan-code, style-code, test-code, review-code) are the same habit for the agent. Both are yours to take home. |
| `AGENTS.md`, `CLAUDE.md` | The agent's instructions. You don't need to read them. |

## Commands

| Command | What it does |
|---|---|
| `make explore` | Builds the page into `out/` (once the agent has built the tool) |
| `make open` | Opens `out/explorer.html` in your browser |
| `make list` | Lists columns, units and missing counts (once the tool has `--list`) |
| `make test` / `make coverage` | Runs the tests / shows lines no test runs |
| `./gate check` | Names the first thing still missing at this level |
| `./gate unlock` | Checks your work and opens the next level |
| `./gate hint` | A hint, unlocking as the level goes on |
| `./gate brief` / `./gate status` | Shows this level's brief / where you are |
