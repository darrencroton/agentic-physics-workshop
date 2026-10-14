# Level 1: Build the prototype

**Target time:** 18 minutes. **Persona in force:** `collaborator`.

## Where we are

`PLAN.md` is committed: your goal, your four decisions, two or three steps and the acceptance criteria. Now build it one step at a time, look at each result yourselves, and commit each step that works. When something breaks, you know which step did it.

`explorer/` is open for editing. `tests/` stays frozen: testing is the next level.

## What to do

1. Make sure Claude is out of plan mode (`Shift+Tab` cycles the modes; the line under the prompt shows which is on). Then the playbook's *Build in checked steps*:

   > "Implement step 1 of PLAN.md only. Run it, show me the exact command and output, and tell me what I can run to check it myself."

2. Run what Claude suggests in the gate terminal and look at the result. Once the page exists, that's `make explore` then `make open`. If it works, ask Claude to commit it.
3. Then: "Next step." Repeat until the plan is done.
4. Run `./gate check` after each step. It names the first thing still missing; paste that line to Claude.
5. When it passes, play with the page for two minutes: rotate, zoom, hover, switch columns, palettes and log axes. Each of you names one feature you'd add, and the Scribe writes them in `LOG.md`. Don't build them now.

## If it goes differently

- A command doesn't work yet (`make list` before the tool has `--list`, say): that part isn't built yet. Ask Claude which step adds it.
- A step is too big to finish cleanly: ask Claude to stop, show what works, and commit that much. Then carry on.
- Claude starts on the next step unasked: the Driver presses `Esc` and asks for one step.
- Claude seems unsure of a plotly detail: "check the installed version's documentation".

## What to watch for

- "This should work now" with no command and output. The Sceptic asks for them.
- `./gate check` saying `data.json` is not valid JSON. That's a real bug, and one Python makes easy. Paste the sentence to Claude.
- Hover showing another row's values after sampling, or a colour bar with no unit. Only someone looking at the browser catches these.

## Opening the gate

`./gate check` runs your tool four times on the `PLAN.md` dataset: with the defaults, with `--max-points 500`, with `--list`, and on a file that does not exist. It checks `data.json` and the page's controls against the README, and needs at least **2 commits** since Level 0 with nothing uncommitted under `explorer/` or in `PLAN.md`.

`./gate unlock` asks a question about your dataset that sends you to the page. A wrong answer gives you a hint: discuss it, then run `./gate unlock` again.

The reflection (logged): each of you, one feature you would add, and which the group liked best.

When the check passes and you've all looked at the page: commit, then `./gate unlock`.
