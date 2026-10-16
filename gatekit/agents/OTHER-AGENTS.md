# Using another agent

These exercises are built for Claude Code, which enforces the rules with hooks. Your agent gets the same rules from `AGENTS.md` but won't be held to them, so please keep to them: the gates still check the work.

Before you start, ask your agent "What may you not do in this repo?" It should list the Never items from `AGENTS.md`. Use a fast, capable mid-tier coding model: the timings were set on Claude Sonnet.

- **Plan (Level 0).** Discuss the plan in your agent's plan or ask mode, if it has one (Codex: `/plan`; Cursor and Copilot: Shift+Tab; OpenCode: the `plan` agent). Once you approve the plan, leave that mode and ask the agent to save and commit `PLAN.md` only, without starting the build.
- **At the start, and after each unlock.** Ask your agent to run `./gate brief` (after an unlock, tell it the level has changed).
- **Skills.** They are in `.claude/skills/`. If your agent doesn't list them, ask it to read `.claude/skills/<name>/SKILL.md` and follow it.
- **Review (Level 3).** The review needs fresh eyes. If your agent can't run the review skill in a fresh context, open a second, new session in this same folder and paste in:

  > Read `.claude/skills/review-code/SKILL.md` and follow it to review the commits since the start tag against `PLAN.md` and `README.md`: three to five findings, ranked. Don't edit anything.

  Then paste its findings back to your main session for `REVIEW.md`.
- **Commits.** The gates count commits. If your agent can't commit, the Driver commits in the gate terminal.
- **Every command refused with a hook error?** Your agent is running Claude Code's hooks. Turn that off: in Copilot CLI set `"disableAllHooks": true` in `~/.copilot/config.json`; in Cursor turn off "Include Third-Party Plugins, Skills, and Other Configs". If the skills disappear too, use the Skills tip above.
