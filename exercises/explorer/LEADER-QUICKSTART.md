# Explorer: group leader quickstart

Private: contains the gate answer. Don't share it with your group.

You run the exercise for one small group on your laptop. It lasts about 45 minutes: the agent builds a browser tool that plots any columns of a dataset in 2D or 3D, and the group practises the habit of **plan, build in checked steps, test, review**. The repo directs the group step by step, so your job is to keep the laptop running and the group moving. Everything here is detailed in `FACILITATOR-WALKTHROUGH.md`.

## Before the day

You need your own laptop running macOS or Linux, with a terminal, git, `make`, Python 3.11+ and a browser, plus the agentic coding tool you already use. Claude Code is preferred; Codex, Cursor, VS Code with Copilot or any command-line agent is fine. Then:

- [ ] A git identity (`git config --global user.name` and `user.email`).
- [ ] Your agent tool signed in. If you don't already pay for an AI subscription, the facilitator gives you Claude Pro.
- [ ] Cloned the bundle; `./preflight` (first run sets up `.venv`: needs the network, about a minute) ends with "Preflight passed". It also checks the skill and agent files.
- [ ] Claude Code only: in `claude`, accept the trust dialog; `/hooks` lists four events, and `/model` to another model is refused. Any other tool: read `OTHER-AGENTS.md`, and ask your agent "What may you not do in this repo?"
- [ ] Rehearsed Level 0, then `./gate reset`.
- [ ] Came to the facilitator's short set-up session.

## On the day

**Opening (60 seconds):** "We build a real tool, a 3D explorer for our data, the way you'd want a careful student to: plan, build in two checked steps, test, review, and commit as we go. The agent is a normal, helpful collaborator; the gates just make sure we do each step. The gate terminal is ours, and the agent can't type there. Hands off the code: we read, look and decide."

**Roles.** Everyone takes one, you included. The Driver rotates at each gate.

| Group | Roles |
|---|---|
| 2 | Driver; Navigator, Sceptic and Scribe (swap at each gate) |
| 3 | Driver, Sceptic, Navigator and Scribe |
| 4 | Driver, Navigator, Sceptic, Scribe |
| 5 | Driver, Navigator, Browser Sceptic, Evidence Sceptic, Scribe |

**Two windows and a browser:** the agent window (Driver only); a separate gate terminal for the humans (`./gate`, `make open`, `make test`), not the agent's own terminal; the browser (`make open`).

**Checkpoints** (minutes from Go): 8 plan committed; 26 Level 1 passed; 34 tests running; 42 review triaged (3 spare). Behind? Narrow to what `./gate check` names.

## Level by level

Every gate ends with a "Talk it over" prompt: nothing to type. Ask it aloud and let the group answer for 30 seconds. Some checks only print a `Note:` and still pass: read it out, it says what is worth doing next time.

**Level 0, Plan (8 min).** Set the dataset first: `./gate dataset pulsars` or `./gate dataset dimuons`, before the plan is committed. Goal: two steps, four decisions, acceptance criteria, committed. Good looks like: the group, not the agent, chose what happens to zeros on a log axis and what the page opens on. Nudge: "Which decisions did the agent make for you?" Exactly two steps is strict; if there are more, merge them (command line and `data.json`, then the page).

**Level 1, Build (18 min).** Goal: two cycles of step, run, look, commit. Good looks like: once the page exists, someone opens it in the browser before it is committed. Nudge: "Show me in the browser. Is it committed?" `NaN` in `data.json` is the classic bug: paste the check's sentence to the agent. Unlock question: pulsars, plot `XX`, `YY`, `ZZ` and rotate: answer **sun**. Dimuons, `M` against `pt1` on log axes: answer **jpsi**. (A wrong answer prints a hint.)

**Level 2, Test (8 min).** Goal: the group's list first, then the agent's plan, then at least five passing tests. Good looks like: the group notices something the agent's plan missed, or the reverse. Nudge: "What can't pytest see?" A failing test is a finding: fix the code, not the test.

**Level 3, Review (8 min).** Goal: two guesses first, then the reviewer's findings, triaged by the group. Good looks like: a REJECT with a good reason, or a fix with a test that fails first. Nudge: "Which of these matter for a prototype?" Early finishers can build their Level 1 feature.

## When stuck

- A guard or gate refusal: read it aloud. It is usually the lesson and it names the fix.
- A command says it is for humans: use a fresh terminal window, not the agent's shell.
- The agent is going in circles after two failed corrections: start a fresh session (`/clear` in Claude Code) with a better prompt that includes what you learned.
- A stuck group: hints first (`./gate hint`), then call the facilitator, who holds the master passphrase for `./gate skip --master` (plus `./gate install-solution --master`).
- Hints: three tiers over time; Level 1 gets a fourth with the answer.
- Page blank: open the browser console and paste the error to the agent.
- Claude Code: hooks don't fire, or the agent edits what should be frozen: the trust dialog was missed (`/hooks` is empty). `/exit`, run `claude` again, accept trust.
- Claude Code: the agent names the wrong model: trust `/status`, not what it says. The session is locked to Sonnet.
- Claude Code: a skill or `reviewer` not listed: `/reload-skills`; else `/exit`, run `claude` again, accept trust.
- Another tool: every command refused with a hook error, or a skill missing: see `OTHER-AGENTS.md`.

## After

- `PLAYBOOK.md` and the four skills in `.claude/skills/` are the group's to take home.
- `./gate reset` saves the group's records (state, git log, `LOG.md`, `PLAN.md`, `TESTS.md`, `REVIEW.md`) and the group's code as `work.bundle` (clone it with `git clone work.bundle`) to `.records/<date-time>/` and returns to level 0. `.records` is a hidden folder: reset prints its path (on a Mac, `open .records` shows it in Finder). Send that folder to the facilitator, with the group's one new feature idea. The dataset goes back to pulsars: `./gate dataset dimuons` switches it.
