# Working With a Coding Agent: a Playbook

The agent is a fast, tireless, literal collaborator. You own the decisions and the result.

## 0. Set up
- Put the project's facts in CLAUDE.md: what it is, how to run it, how to test it,
  conventions. Keep it short. `/init` drafts one.
- Use git. One change, one check, one commit. Any step can then be undone.

## 1. Understand (plan mode: Shift+Tab until "plan mode on")
"Read <files>. Summarise what the code and data contain and what the task asks.
 List anything unclear or ambiguous. Don't write any code."

## 2. Define the check, then plan
"Propose a plan: the goal, the decisions it depends on, the design, a few steps
 (two or three for a small job) that each end in something we can run and look at,
 acceptance criteria we can check, and what's out of scope. Ask me about any
 decision you're unsure of."
- Read it. Change it. The decisions are yours. Save it as PLAN.md. Commit it.

## 3. Build in checked steps
"Implement step 1 of PLAN.md only. Run it, show me the exact command and output,
 and tell me what I can run to check it myself."
- Run that yourself and look at the result. Commit. Then: "Next step."
- Stop it (Esc) if it starts doing more than one step.

## 4. Evidence: test plan, then tests
- First write your own list: three things that must not break.
"Talk me through the tests this code needs: what each one checks, what coverage
 that gives, and what it won't cover. Don't write them yet."
- Compare with your list. Agree. Then:
"Write them. Run them and show me the output."
- Run them yourself. Look at the coverage report.
"Break <one behaviour> on purpose and run the tests. Do they fail? Then revert."
- Never accept a test changed just to make it pass.

## 5. Independent review
- First write your own guess: two things a reviewer will find.
"Use a subagent with no context from this session to review the code against
 PLAN.md. Rank the findings by severity. Don't fix anything."
  (or /code-review, which does the same on the current diff)
- Decide the findings that matter: FIX, ACCEPT or REJECT, with a reason.
  Many low ones? Triage the top few; the rest can wait.
"Fix the FIX items one at a time. For each, add a test that fails before the fix
 and passes after, then run the tests." Commit each.

## 6. Recover
- Esc stops it. Esc Esc or /rewind undoes. After two failed corrections: /clear and
  write a better prompt that includes what you learned.

## Red flags
- "Done" or "all tests pass" with no command and output shown.
- A test or tolerance changed to make a failure go away.
- Code that does more than the plan says.
- Confident use of a library API: "check the installed version's documentation".
- You can't explain what the code does. Ask it to, then check.

## Make it stick (optional)
- A reviewer agent: copy .claude/agents/reviewer.md from this repo into your project.
- A Stop hook that runs your tests, so the agent cannot finish with them failing
  (exit code 2 blocks; a failing pytest exits 1, so wrap it):
  {"hooks": {"Stop": [{"hooks": [{"type": "command",
    "command": "sh -c 'cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/pytest -q || exit 2'"}]}]}}
  in .claude/settings.json. Add it once tests exist.
