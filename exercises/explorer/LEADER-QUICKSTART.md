# Explorer: group leader quickstart

Private: contains the gate answer. Don't share it with your group.

You coach one group through a 45-minute exercise: the agent builds a browser tool that plots any columns of a dataset in 2D or 3D, and the group runs the habit of **plan, build in checked steps, test, review**. You ask questions and fix tooling; you don't drive. Everything here is detailed in `FACILITATOR-WALKTHROUGH.md`.

## Before the day

- [ ] A Mac with Xcode Command Line Tools, Python 3.11+, a browser, and a git identity (`git config --global user.name` and `user.email`).
- [ ] Claude Code 2.1.295 or newer, signed in, able to use Sonnet.
- [ ] Clone the bundle, run `./preflight` (first run sets up `.venv`: needs the network, about a minute): it must end with "Preflight passed".
- [ ] Run `claude` in the repo, accept the trust dialog, and check `/hooks` lists four events and `/status` says Sonnet.
- [ ] Set the `Dataset:` line of `PLAN.md` (`data/pulsars.csv` or `data/dimuons.csv`) and leave it uncommitted.
- [ ] Rehearse Level 0, then reset (walkthrough section 7).

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

**Level 0, Plan (8 min).** Goal: two steps, four decisions, acceptance criteria, committed. Good looks like: the group, not the agent, chose what happens to zeros on a log axis and what the page opens on. Nudge: "Which decisions did the agent make for you?" Exactly two steps is strict; if there are more, merge them (command line and `data.json`, then the page).

**Level 1, Build (18 min).** Goal: two cycles of step, run, look, commit. Good looks like: once the page exists, someone opens it in the browser before it is committed. Nudge: "Show me in the browser. Is it committed?" `NaN` in `data.json` is the classic bug: paste the check's sentence to the agent. Unlock question: pulsars, plot `XX`, `YY`, `ZZ` and rotate: answer **sun**. Dimuons, `M` against `pt1` on log axes: answer **jpsi**. (A wrong answer prints a hint.)

**Level 2, Test (8 min).** Goal: the group's list first, then the agent's plan, then at least five passing tests. Good looks like: the group notices something the agent's plan missed, or the reverse. Nudge: "What can't pytest see?" A failing test is a finding: fix the code, not the test.

**Level 3, Review (8 min).** Goal: two guesses first, then the reviewer's findings, triaged by the group. Good looks like: a REJECT with a good reason, or a fix with a test that fails first. Nudge: "Which of these matter for a prototype?" Early finishers can build their Level 1 feature.

## When stuck

- `./gate hint` in the gate terminal: three tiers over time; Level 1 gets a fourth with the answer.
- Still stuck: `./gate skip --master` needs the facilitator, who holds the passphrase. Call them over.
- Agent going in circles after two failed corrections: `/clear` for a fresh session and a better prompt.
- A command refused by the guard: the agent shouldn't reword it. Let it use a `make` target instead.
- `./gate` says it is "for humans": use a fresh Terminal window, not one opened from Claude Code.
- Page blank: open the browser console and paste the error to the agent.
- A skill or `reviewer` not listed: `/reload-skills`; else exit, reopen `claude`, accept trust.

## After

- Copy out `LOG.md`, `TESTS.md`, `REVIEW.md` and `git log --oneline` for the show-and-tell. Send the group's one new feature idea along.
- `PLAYBOOK.md` and the four skills in `.claude/skills/` are the group's to take home.
- Reset: `./gate reset`, then `git reset --hard start && git clean -fdx -e .venv -e .workshop`, and set the `Dataset:` line again.
