# Working With a Coding Agent: a Playbook

The agent is a fast, tireless, literal collaborator. You own the decisions and the result.

## 0. Set up
- Put the project's facts in AGENTS.md: what it is, how to run it, how to test it,
  conventions. Keep it short, and let the agent draft it. Claude Code reads it too
  if there is no CLAUDE.md.
- Use git. One change, one check, one commit. Any step can then be undone.

## 1. Understand (plan mode on; Shift+Tab in Claude Code)
"Read <files>. Summarise what the code and data contain and what the task asks.
 List anything unclear or ambiguous. Don't write any code."

## 2. Define the check, then plan
"Using the plan-code skill, propose a plan: the goal, the decisions it depends
 on, the design, a few steps (two or three for a small job) that each end in
 something we can run and look at, acceptance criteria we can check, and what's
 out of scope. Ask me about any decision you're unsure of."
- Read it. Change it. The decisions are yours. Save it as PLAN.md. Commit it.

## 3. Build in checked steps
"Implement step 1 of PLAN.md only, following the coding guidelines in the
 style-code skill. Run it, show me the exact command and output, and tell me what
 I can run to check it myself."
- Run that yourself and look at the result. Commit. Then: "Next step."
- Stop it (Esc in Claude Code) if it starts doing more than one step.

## 4. Evidence: test plan, then tests
- First write your own list: three things that must not break.
"Using the test-code skill, talk me through the tests this code needs: what each
 one checks, what coverage that gives, and what it won't cover. Don't write them
 yet."
- Compare with your list. Agree. Then:
"Write them. Run them and show me the output."
- Run them yourself. Look at the coverage report.
"Break <one behaviour> on purpose and run the tests. Do they fail? Then revert."
- Never accept a test changed just to make it pass.

## 5. Independent review
- First write your own guess: two things a reviewer will find.
"Use the review-code skill to review the code against PLAN.md. Rank the findings
 by severity. Don't fix anything."
- It runs in a fresh context (a subagent in Claude Code) with no memory of this session. That is the point.
- Decide the findings that matter: FIX, ACCEPT or REJECT, with a reason.
  Many low ones? Triage the top few; the rest can wait.
"Fix the FIX items one at a time. For each, add a test that fails before the fix
 and passes after, then run the tests." Commit each.

## 6. Recover
- Stop it, and undo if needed (in Claude Code: Esc, then Esc Esc or /rewind). After
  two failed corrections, start a fresh session (/clear in Claude Code) and write a
  better prompt that includes what you learned.

## Red flags
- "Done" or "all tests pass" with no command and output shown.
- A test or tolerance changed to make a failure go away.
- Code that does more than the plan says.
- Confident use of a library API: "check the installed version's documentation".
- You can't explain what the code does. Ask it to, then check.

## Make it stick (optional)
- The four skills: copy .claude/skills/ from this repo into your project (Claude
  Code, Cursor, Copilot and OpenCode read it; Codex and Antigravity read
  .agents/skills/), or into ~/.claude/skills/ for every Claude Code project. Each
  SKILL.md says what it does and how to call it.
- A Stop hook that runs your tests, so the agent cannot finish with them failing.
  Claude Code example (exit code 2 blocks; a failing pytest exits 1, so wrap it):
  {"hooks": {"Stop": [{"hooks": [{"type": "command",
    "command": "sh -c 'cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/pytest -q || exit 2'"}]}]}}
  in .claude/settings.json. Add it once tests exist.
