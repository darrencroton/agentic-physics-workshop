# Level 0: Plan

**Target time:** 8 minutes.

## Where we are

No code yet. The agent starts in **plan mode**: it reads and proposes, but changes nothing (`Shift+Tab` cycles the modes). Agree a plan, write it in `PLAN.md`, and commit it. Your leader has already set its `Dataset:` line.

## Do this

1. In the agent window, type:

   > "Read INTERFACE.md, data/README.md and the column file for our dataset. Say what the data contains, which columns have missing values and how many, and anything unclear. Then, using the plan-code skill, propose a plan: the goal, the decisions it depends on, the design, two build steps that each end in something we can run and look at, acceptance criteria we can check, and what's out of scope. Ask me about any decision you're unsure of. Don't write any code."

2. Read it. Argue about it. Change it. The four decisions in `PLAN.md` are the group's, not the agent's. The Sceptic owns the acceptance criteria (aim for three or more, each checkable by eye or by test). The Navigator cuts anything beyond the interface.
3. Approve the plan. Ask the agent to write it into `PLAN.md`, keeping the template's headings and the `Dataset:` line exactly as they are, then to commit it.
4. Run `./gate check` in the gate terminal. It names the first thing still missing.

## Watch for

- Two steps only. If there are more, ask the agent to merge them: the command line, `--list` and `data.json` first; then the page.
- Decisions made silently: dropping rows, clipping logs, which columns the page opens on. Each belongs in `PLAN.md`, decided by you.
- A plan bigger than the job (class hierarchies, config systems). It's a prototype.
- The agent asks something nobody knows: pick a reasonable answer, write it down, move on. If it tries to write code, the guard refuses, on purpose.

## The gate

`PLAN.md` filled in, with exactly two steps, and committed. When `./gate check` passes, run `./gate unlock`. A talk prompt follows.
