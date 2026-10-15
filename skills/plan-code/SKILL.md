---
name: plan-code
description: Plan a coding task before any code is written. Read first, surface the decisions, then write a short PLAN.md with steps that end in something runnable and acceptance criteria a person can check. Use when asked for a plan, to plan a change, or for the plan-code skill.
---

# Plan the work before the code

A plan is a short written agreement about what will be built, in what order, and how you will both know it works. Writing it first turns the agent's silent assumptions into decisions the human makes. Nothing is implemented in this skill.

## Steps

1. **Read before planning.** Read the files, data and docs the task names, and the project's `README.md` and `CLAUDE.md` if they exist. Run the existing tests or the tool once if that is cheap. Say in a few lines what you found and list anything unclear.
2. **Ask, do not assume.** Every choice you would otherwise make silently is a decision for the human: edge cases in the data (missing values, zeros, empty input), defaults, which library, what the first version leaves out. Put each one as a question with your recommended answer, and wait.
3. **Propose the plan** in the format below. Size it to the job: as few steps as the work needs, each ending in something the human can run and look at.
4. **Revise until approved.** The human may change anything. Record the decisions as they were made, not as you proposed them.
5. **Write and commit.** On approval, write `PLAN.md` and offer to commit it on its own, so the plan is in the history before any code.

## PLAN.md

If the project already has a `PLAN.md` template, keep its headings and any lines it sets, and fill it in. Otherwise:

```markdown
# Plan

## Goal
One or two sentences: what will exist when this is done, and for whom.

## Decisions
- <decision>: <the answer the human chose>

## Design
The files or modules to add or change, one line each on what it does.

## Steps
1. <step>: ends in `<command>`, showing <what to look for>
2. ...

## Acceptance criteria
- <one checkable assertion>, checked by `<command>` or by looking at <what>

## Out of scope
- <what this plan deliberately does not do>
```

## Rules

- A step ends in something runnable. "Set up the package" is not a step; "`python -m tool --list` prints the columns" is.
- An acceptance criterion is one assertion per line that a person can check, with how. "Works correctly" is not one; "a missing input file gives a one-line error and exit code 1" is.
- Name the files the work may touch. Touching anything else needs a new decision.
- Out of scope is a real list. Say what was cut, so nobody builds it by accident.
- Prefer the boring design: no class hierarchies, configuration systems or abstractions the steps do not need.
- Do not write code, tests or scratch scripts while planning. If the task is too unclear to plan, say what is missing and stop.
