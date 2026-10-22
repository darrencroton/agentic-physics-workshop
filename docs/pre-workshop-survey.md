# Pre-Workshop Email and Survey

A reusable invitation email and attendee survey for the "Agentic AI for physics research" session. They do two jobs:

1. **Find out who is coming:** experience, views, worries and expectations, so you can pitch the short lecture and spread experience across groups.
2. **Recruit Explorer group leaders.** A large workshop needs 30–40, so the bar is kept low. The email asks for leaders directly ("reply to me"), because many people skip surveys. The survey asks as well.

Everything in `{{BRACES}}` changes for each workshop; the rest stays the same.

## How to use it

1. Fill in the details for the workshop (section 5, "Before you send").
2. Create the survey with the Google Apps Script (section 4) and copy its link.
3. Send the email (section 2) from your own address, so that leader replies come to you.
4. A week later, send a two-line reminder: the survey link, and "still looking for about {{N}} more group leaders; reply if you can help".
5. After the survey closes, use the responses to pitch the lecture. Send volunteers the exercise bundle, the leader quickstart and a time for the set-up session (`README.md`, "Run the workshop", step 5).
6. After the session, run the feedback form (`docs/00-facilitator-guide.md` §9). Its confidence question matches survey question 8, so you can measure the change.

---

## 1. What a group leader needs

The role: run the Explorer exercise for a small group on your own laptop. The exercise guides the group step by step, so leading mostly means keeping the laptop running and the group moving. Leaders get set-up instructions by email for whichever tool they use, and a short set-up session beforehand.

A leader needs:

- **Their own laptop**, brought on the day. Mac or Linux is preferred: the exercise needs a Unix-style terminal, and Windows is not supported.
- **Some experience with an AI coding agent** in a tool of their choice, or a willingness to get some before the day. Any tool will do: the Claude app or Claude Code, Codex, Cursor, VS Code with Copilot, a command-line agent or similar. Claude Code is preferred.
- **Enough terminal experience** to set up the exercise from instructions, and to keep their laptop running for the group.
- **About an hour beforehand** to set up from the emailed instructions and attend the short set-up session.
- **An AI subscription.** Leaders who don't already pay for one (Claude, ChatGPT, Gemini, Copilot or similar) are given a Claude Pro subscription.

**How many:** one leader per group of 3–5, so about one per four attendees, plus a spare or two.

---

## 2. The email

> **Subject:** {{WORKSHOP_NAME}}: AI agents for physics research. A 2-minute survey, and group leaders wanted
>
> Hi all,
>
> At {{WORKSHOP_NAME}} on {{SESSION_DATE}} I'm running a 60-minute hands-on session on using AI coding agents in physics research. In small groups, you'll direct an agent to build a small, real tool from a public dataset, and practise the habits that keep its work trustworthy: plan, build in checked steps, test and review. All levels of experience are welcome, sceptics included.
>
> **Two quick asks:**
>
> **1. A 2-minute survey** so I can pitch the session to the room: {{SURVEY_LINK}}
> Please fill it in by **{{SURVEY_DEADLINE}}**, even if you've never used these tools. Those answers matter just as much.
>
> **2. Group leaders wanted: please reply to this email.**
> I need about {{N_LEADERS}} people to each run the exercise for a small group on their own laptop. The exercise guides the group step by step, so leading mostly means keeping the laptop running and the group moving. You'll need:
>
> - your own laptop to bring on the day (Mac or Linux preferred);
> - some experience with an AI coding agent in whatever tool you like (Claude, Codex, Cursor, Copilot, a command-line agent and so on), or a willingness to get some before the day;
> - enough terminal experience to set up the exercise from instructions;
> - about an hour beforehand: setting up from instructions I'll email you, and a short set-up session with me.
>
> If you don't already have a paid AI subscription, I'll provide a Claude Pro subscription for the month.
>
> Interested? **Just reply by {{LEADER_DEADLINE}}** and tell me which agent tool you use, if any, and whether your laptop is a Mac, Linux or Windows. "Maybe, tell me more" is a fine reply.
>
> Thanks, and see you there,
> {{YOUR_NAME}}

---

## 3. The survey

**Ten questions, about two minutes.** It's anonymous: there's no sign-in, and emails are collected only from people who volunteer to lead. Every question is there because its answers change something about the session; the note in italics says what. Only questions 2 and 10 are required, to keep drop-off low.

1. **Career stage.** Undergraduate / Masters student · PhD student · Postdoc / fellow · Permanent staff · Technical / RSE · Other.
   *Pitch: supervisors and students need different emphasis, for example on supervising students who use AI.*
2. **Which have you used for coding? (tick all that apply)** *(required)*
   - None yet
   - Chat in a browser or app: paste code in, copy answers back (ChatGPT, Claude, Gemini and the like)
   - Suggestions in my editor: autocomplete or inline edits (Copilot, Cursor and the like)
   - A desktop AI app that edits my files and runs code itself (Claude or Codex app and the like)
   - An agent in my editor that edits files and runs commands (Cursor or Copilot agent mode and the like)
   - An agent in the terminal (Claude Code, Codex CLI, Gemini CLI and the like)
   *Shows how much of the room has used an agent, and where they use it. Apps, editor agents and terminal agents do much the same job, so they aren't ranked against each other.*
3. **How often do you use AI for coding?** Never · Tried it · Monthly · Weekly · Daily.
   *Depth of experience: pitch the lecture, and spread experienced people across groups.*
4. **How comfortable are you using a terminal (the command line)?** Never used one · Get by · Comfortable.
   *Pitch the set-up steps, and spot potential leaders who didn't volunteer.*
5. **Overall, how do you feel about AI tools in research?** 1–5, from *very sceptical* to *very enthusiastic*.
   *The lecture's tone.*
6. **What worries you most?** Pick up to two: Plausible but wrong results · Reproducibility · Losing skills (or students not learning them) · Data privacy · Authorship / plagiarism · Environmental cost · Hype and wasted time · Nothing much · Other.
   *The lecture's "you own the science" slide tackles the top answers directly.*
7. **What do you most want from the session?** Pick up to two: See what an agent can really do · Hands-on practice · Habits for checking its work · Ideas for my own code · Its limits and risks · Advice for supervising students who use AI · Other.
   *Where the lecture's time goes.*
8. **How confident are you that you could use an AI agent productively on your own research code right now?** 1–5.
   *Asked again, with the same wording, in the post-session feedback form (`docs/00-facilitator-guide.md` §9, Q4), so you can measure the change.*
9. **Anything you'd like covered, or that I should know (including access needs)?** Optional free text.
10. **Could you lead a group?** *(required)* Shows the list from section 1. Yes · Maybe, tell me more · No thanks.
    **Yes or Maybe goes to a second page with three questions:**
    - *Your email* (required).
    - *Your laptop:* Mac · Linux · Windows (required). *Tells you early whether you have enough Mac and Linux leaders.*
    - *Which AI coding tool and subscription do you use?* (optional). *Tells you how many Claude Pro subscriptions you need, and which instructions to send.*

---

## 4. Setting it up in Google Forms

The script [`tools/survey/pre-workshop-survey.gs`](../tools/survey/pre-workshop-survey.gs) builds the survey above, with its branching, and a linked response Sheet. Each run makes a fresh form, so each workshop gets its own form and its own responses.

1. Open [script.google.com](https://script.google.com), signed in to the Google account that should own the form, and create a **New project**.
2. Replace the editor's contents with the script, and fill in the settings at the top: `WORKSHOP_NAME`, `SESSION_DATE` and, if you need one, `CONSENT_TEXT`.
3. Choose the `buildSurvey` function and click **Run**. The first run asks for permission to create forms and spreadsheets in your Drive.
4. The execution log prints the links to edit the form, to fill it in, and to the response Sheet. Open the edit link, check it with **Preview**, and click **Publish** if Google Forms shows that button.
5. Paste the fill-in link into the email as `{{SURVEY_LINK}}`.

If the survey questions change, update both this document and the script.

---

## 5. Before you send

- [ ] **Details for this workshop:** workshop name and session date, the survey and leader deadlines, the number of leaders needed (`{{N_LEADERS}}`, about one per four attendees), and dates for the set-up sessions.
- [ ] **Claude Pro for leaders:** decide who pays, and how subscriptions reach leaders who need one.
- [ ] **Ethics:** if the results will be presented or published beyond the workshop, check whether your institution needs ethics approval. If it needs a consent statement, put it in `CONSENT_TEXT`.
- [ ] **Timeline:** a suggestion working back from the session:
  - send the email about four weeks before;
  - survey closes two weeks before;
  - leaders confirmed about three weeks before;
  - bundles and instructions go to leaders two weeks before;
  - set-up sessions in the week before.
- [ ] **Windows:** the exercise uses `make`, shell launchers and a Python virtual environment laid out for macOS and Linux, so native Windows doesn't work. If you're short of leaders, or many Windows users volunteer, WSL2 (Linux inside Windows) is the likely route, but it is untested.
