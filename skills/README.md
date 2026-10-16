# Four skills for working with a coding agent

Four small, general skills for coding agents (the Agent Skills format) that make a good agentic coding workflow a habit: plan first, write readable code, test what must not break, and get an independent review. They are written for anyone whose code is mostly small scientific tools, and they do not depend on any project, tool or workshop.

| Skill | What it does | How to call it |
|---|---|---|
| `plan-code` | Reads first, surfaces every decision, writes a short `PLAN.md` with runnable steps and checkable acceptance criteria. No code. | "... using the plan-code skill" |
| `style-code` | Guidelines for structure, names, comments, errors and numbers. Applies them while writing, or audits changed files without editing them. | "... following the style-code skill", or "Audit these files with the style-code skill" |
| `test-code` | Agrees a test plan before any test is written, tests behaviour through the public interface, and shows that a test can fail. | "... using the test-code skill" |
| `review-code` | A fresh-context review (a subagent in Claude Code) that has not seen the conversation: ranked findings with file and line, nothing edited. You decide what to do with each. | "Review ... using the review-code skill" |

Name the skill in your prompt (in Claude Code you can also type `/plan-code`, `/review-code` and so on).

Each skill is one `SKILL.md` file. Open it and read it: it is short, and it says what it will and will not do.

## Install

Agents read skills from two places. Pick one.

| Agent | One project | Every project |
|---|---|---|
| Claude Code | `.claude/skills/` (Cursor, Copilot and OpenCode read it too) | `~/.claude/skills/` |
| Codex, Antigravity (and most others) | `.agents/skills/` | see your agent's docs (Codex: `~/.agents/skills/`) |

- **One project:** copy the four directories into the folder above at the project root, so `.claude/skills/plan-code/SKILL.md` and so on. Commit them, and everyone who clones the project gets them.
- **Every project:** copy them into the user-level folder (or symlink: `ln -s "$(pwd)/skills/plan-code" ~/.claude/skills/plan-code`).

In Claude Code, a new skills directory is picked up at the next start of `claude`, or straight away with `/reload-skills`. Type `/` to see them listed.

## A typical session

1. "Plan this using the plan-code skill: <the task>." Argue with the plan, change it, commit it.
2. "Implement step 1 of PLAN.md only, following the style-code skill. Run it, show me the command and output, and tell me what I can run to check it." Look, commit, "Next step."
3. "Using the test-code skill, talk me through the tests this code needs." Agree the plan, then "Write them."
4. "Review the changes since <base> using the review-code skill." Decide each finding; fix the ones that matter, each with a test that fails first.

The skills are the habit written down. The decisions stay yours.

## Make it stick

- The Guidelines section of `style-code` is short enough to paste into a project's `AGENTS.md` (or `CLAUDE.md`), which applies it to every session without naming the skill.
- Once tests exist, a Stop hook that runs them stops the agent finishing with them failing. Claude Code example, in `.claude/settings.json` (a failing pytest exits 1, and only exit code 2 blocks, so wrap it):

  ```json
  {"hooks": {"Stop": [{"hooks": [{"type": "command",
    "command": "sh -c 'cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/pytest -q || exit 2'"}]}]}}
  ```


## Edit them

They are plain Markdown. If a rule does not fit your project, change it. Keep each skill short: a skill the agent reads in ten seconds is one it follows.
