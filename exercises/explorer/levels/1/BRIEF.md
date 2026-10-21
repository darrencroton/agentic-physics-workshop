# Level 1: Build the prototype

**Target time:** 18 minutes.

## Where we are

`PLAN.md` is committed. Now build it one step at a time, look at each result yourselves, and commit each step that works. `explorer/` is open; `tests/` stays frozen until Level 2.

## Do this

1. Make sure the agent is out of plan mode (`Shift+Tab`). Then:

   > "Implement step 1 of PLAN.md only, following the coding guidelines in the style-code skill. Run it, show me the exact command and output, and tell me what I can run to check it myself."

2. Run what the agent suggests in the gate terminal and look. Once the page exists, that's `make explore` then `make open`. If it works, ask the agent to commit it.
3. Say "Next step", and repeat until the plan is done.
4. Run `./gate check` after each step and paste its first line to the agent.
5. When it passes, play with the page for a minute: rotate, zoom, hover, switch columns, palettes and log axes. The Scribe notes one feature you'd add in `LOG.md`. Don't build it now.

## Watch for

- "This should work now" with no command and output. The Sceptic asks for both. If the agent starts the next step unasked, the Driver stops it (`Esc`).
- `data.json` "not valid JSON": a real bug, and one Python makes easy. Paste the sentence to the agent.
- Hover showing another row's values after sampling, or a colour bar with no unit. Only someone looking at the browser catches these.

## The gate

`./gate check` runs your tool four times and checks `data.json` and the page's controls against `INTERFACE.md`. It needs at least 2 commits since Level 0 and nothing uncommitted under `explorer/` or in `PLAN.md`. Once it passes and you've all looked at the page: commit, then `./gate unlock`. It asks one question that sends you to the page; a wrong answer gives a hint, so discuss it and try again. A talk prompt follows.
