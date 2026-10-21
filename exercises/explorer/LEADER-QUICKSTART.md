# Explorer: group leader quickstart

Private: contains the gate answer. Don't share it with your group.

You coach one group through a 45-minute exercise: the agent builds a browser tool that plots any columns of a dataset in 2D or 3D, and the group runs the habit of **plan, build in checked steps, test, review**. You ask questions and fix tooling; you don't drive. Everything here is detailed in `FACILITATOR-WALKTHROUGH.md`.

## Before the day

- [ ] A Mac with Xcode Command Line Tools, Python 3.11+, a browser, and a git identity (`git config --global user.name` and `user.email`).
- [ ] Claude Code 2.1.295 or newer, signed in, able to use Sonnet.
- [ ] Cloned the bundle; `./preflight` (first run sets up `.venv`: needs the network, about a minute) ends with "Preflight passed". It also checks the skill and agent files.
- [ ] In `claude`, accept the trust dialog; `/hooks` lists four events, and `/model` to another model is refused.
- [ ] Rehearsed Level 0, then `./gate reset`.

## On the day

**Opening (60 seconds):** "We build a real tool, a 3D explorer for our data, the way you'd want a careful student to: plan, build in two checked steps, test, review, and commit as we go. The agent is a normal, helpful collaborator; the gates just make sure we do each step. The gate terminal is ours, and the agent can't type there. Hands off the code: we read, look and decide."

**Roles** (you are always Coach; the Driver rotates at each gate, and never you unless there are two of you):

| Group | Roles |
|---|---|
| 2 | You: Navigator. Other: Driver, Sceptic, Scribe |
| 3 | Driver, Sceptic. You: Navigator, Scribe |
| 4 | Driver, Navigator, Sceptic. You: Scribe |
| 5 | Driver, Navigator, Browser Sceptic, Evidence Sceptic. You: Scribe |

**Two windows and a browser:** the agent window (Claude Code, Driver only); a separate gate terminal opened from Terminal, not from Claude Code (`./gate`, `make open`, `make test`); the browser (`make open`).

**Checkpoints** (minutes from Go): 8 plan committed; 26 Level 1 passed; 34 tests running; 42 review triaged (3 spare). Behind? Narrow to what `./gate check` names.

## Level by level

Every gate ends with a "Talk it over" prompt: nothing to type. Ask it aloud and let the group answer for 30 seconds. Some checks only print a `Note:` and still pass: read it out, it says what is worth doing next time.

**Level 0, Plan (8 min).** Set the dataset first: `./gate dataset pulsars` or `./gate dataset dimuons`, before the plan is committed. Goal: two steps, four decisions, acceptance criteria, committed. Good looks like: the group, not the agent, chose what happens to zeros on a log axis and what the page opens on. Nudge: "Which decisions did the agent make for you?" Exactly two steps is strict; if there are more, merge them (command line and `data.json`, then the page).

**Level 1, Build (18 min).** Goal: two cycles of step, run, look, commit. Good looks like: once the page exists, someone opens it in the browser before it is committed. Nudge: "Show me in the browser. Is it committed?" `NaN` in `data.json` is the classic bug: paste the check's sentence to the agent. Unlock question: pulsars, plot `XX`, `YY`, `ZZ` and rotate: answer **sun**. Dimuons, `M` against `pt1` on log axes: answer **jpsi**. (A wrong answer prints a hint.)

**Level 2, Test (8 min).** Goal: the group's list first, then the agent's plan, then at least five passing tests. Good looks like: the group notices something the agent's plan missed, or the reverse. Nudge: "What can't pytest see?" A failing test is a finding: fix the code, not the test.

**Level 3, Review (8 min).** Goal: two guesses first, then the reviewer's findings, triaged by the group. Good looks like: a REJECT with a good reason, or a fix with a test that fails first. Nudge: "Which of these matter for a prototype?" Early finishers can build their Level 1 feature.

## When stuck

- A command says it is for humans: use a fresh Terminal window, not Claude Code's shell.
- Hooks don't fire, or the agent edits what should be frozen: the trust dialog was missed (`/hooks` is empty). `/exit`, run `claude` again, accept trust.
- The agent names the wrong model: trust `/status`, not what it says. The session is locked to Sonnet.
- The agent is going in circles after two failed corrections: `/clear` and a better prompt that includes what you learned.
- A guard or gate refusal: read it aloud. It is usually the lesson and it names the fix.
- A stuck group: hints first (`./gate hint`), then call the facilitator, who holds the master passphrase for `./gate skip --master` (plus `./gate install-solution --master`).
- Hints: three tiers over time; Level 1 gets a fourth with the answer.
- Page blank: open the browser console and paste the error to the agent.
- A skill or `reviewer` not listed: `/reload-skills`; else `/exit`, run `claude` again, accept trust.

## After

- `PLAYBOOK.md` and the four skills in `.claude/skills/` are the group's to take home.
- `./gate reset` saves the group's records (state, git log, `LOG.md`, `PLAN.md`, `TESTS.md`, `REVIEW.md`) and the group's code as `work.bundle` (clone it with `git clone work.bundle`) to `.records/<date-time>/` and returns to level 0. `.records` is a hidden folder: `open .records` shows it in Finder, and reset prints its path. Send that folder to the facilitator, with the group's one new feature idea. The dataset goes back to pulsars: `./gate dataset dimuons` switches it.
