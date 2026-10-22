/**
 * Builds the pre-workshop survey (docs/pre-workshop-survey.md, section 3)
 * as a Google Form with a linked response Sheet.
 *
 * Use: paste into a new project at https://script.google.com, fill in the
 * settings below, choose buildSurvey and click Run. Each run creates a new
 * form and Sheet; the links are printed in the execution log.
 *
 * Keep the questions in step with docs/pre-workshop-survey.md.
 */

// Settings for each workshop.
const WORKSHOP_NAME = 'Your Workshop 2026';
const SESSION_DATE = '1 January 2027';
// Optional consent statement shown at the top of the form; leave '' for none.
const CONSENT_TEXT = '';

const LEADER_NEEDS = [
  'The role: run the exercise for a small group on your own laptop. The ' +
    'exercise guides the group step by step, so leading mostly means keeping ' +
    'the laptop running and the group moving. You will need:',
  '- your own laptop to bring on the day (Mac or Linux preferred);',
  '- some experience with an AI coding agent in whatever tool you like ' +
    '(Claude, Codex, Cursor, Copilot, a command-line agent and so on), or a ' +
    'willingness to get some before the day;',
  '- enough terminal experience to set up the exercise from instructions;',
  '- about an hour beforehand: setting up from emailed instructions, and a ' +
    'short set-up session.',
  'If you do not already have a paid AI subscription, a Claude Pro ' +
    'subscription is provided.',
].join('\n');

function buildSurvey() {
  const title = WORKSHOP_NAME + ': AI agents for physics research';
  const form = FormApp.create(title);

  let description =
    'A 2-minute survey before the hands-on session on AI coding agents at ' +
    WORKSHOP_NAME + ' on ' + SESSION_DATE + '. It helps pitch the session ' +
    'to the room. It is anonymous unless you volunteer to lead a group. ' +
    'Answers from people who have never used these tools matter just as much.';
  if (CONSENT_TEXT) {
    description += '\n\n' + CONSENT_TEXT;
  }
  form.setDescription(description)
    .setConfirmationMessage(
      'Thank you! If you volunteered to lead a group, you will hear back by email.')
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false);
  disableEmailCollection(form);

  form.addMultipleChoiceItem()
    .setTitle('Career stage')
    .setChoiceValues([
      'Undergraduate / Masters student', 'PhD student', 'Postdoc / fellow', 'Permanent staff',
      'Technical / RSE'])
    .showOtherOption(true);

  form.addCheckboxItem()
    .setTitle('Which have you used for coding?')
    .setHelpText('Tick all that apply.')
    .setChoiceValues([
      'None yet',
      'Chat in a browser or app: paste code in, copy answers back (ChatGPT, Claude, Gemini and the like)',
      'Suggestions in my editor: autocomplete or inline edits (Copilot, Cursor and the like)',
      'A desktop AI app that edits my files and runs code itself (Claude or Codex app and the like)',
      'An agent in my editor that edits files and runs commands (Cursor or Copilot agent mode and the like)',
      'An agent in the terminal (Claude Code, Codex CLI, Gemini CLI and the like)'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('How often do you use AI for coding?')
    .setChoiceValues(['Never', 'Tried it', 'Monthly', 'Weekly', 'Daily']);

  form.addMultipleChoiceItem()
    .setTitle('How comfortable are you using a terminal (the command line)?')
    .setChoiceValues(['Never used one', 'Get by', 'Comfortable']);

  form.addScaleItem()
    .setTitle('Overall, how do you feel about AI tools in research?')
    .setBounds(1, 5)
    .setLabels('Very sceptical', 'Very enthusiastic');

  form.addCheckboxItem()
    .setTitle('What worries you most?')
    .setHelpText('Pick up to two.')
    .setChoiceValues([
      'Plausible but wrong results', 'Reproducibility',
      'Losing skills (or students not learning them)', 'Data privacy',
      'Authorship / plagiarism', 'Environmental cost',
      'Hype and wasted time', 'Nothing much'])
    .showOtherOption(true)
    .setValidation(atMostTwo());

  form.addCheckboxItem()
    .setTitle('What do you most want from the session?')
    .setHelpText('Pick up to two.')
    .setChoiceValues([
      'See what an agent can really do', 'Hands-on practice',
      'Habits for checking its work', 'Ideas for my own code',
      'Its limits and risks', 'Advice for supervising students who use AI'])
    .showOtherOption(true)
    .setValidation(atMostTwo());

  form.addScaleItem()
    .setTitle('How confident are you that you could use an AI agent ' +
      'productively on your own research code right now?')
    .setBounds(1, 5)
    .setLabels('Not at all', 'Very');

  form.addParagraphTextItem()
    .setTitle('Anything you would like covered, or that I should know ' +
      '(including access needs)?');

  const leadItem = form.addMultipleChoiceItem()
    .setTitle('Could you lead a group?')
    .setHelpText(LEADER_NEEDS)
    .setRequired(true);

  const leaderPage = form.addPageBreakItem()
    .setTitle('Leading a group')
    .setHelpText('Thank you! I will email you with the details.');

  leadItem.setChoices([
    leadItem.createChoice('Yes', leaderPage),
    leadItem.createChoice('Maybe, tell me more', leaderPage),
    leadItem.createChoice('No thanks', FormApp.PageNavigationType.SUBMIT),
  ]);

  form.addTextItem()
    .setTitle('Your email')
    .setValidation(FormApp.createTextValidation()
      .setHelpText('Please enter an email address.')
      .requireTextIsEmail()
      .build())
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Your laptop')
    .setChoiceValues(['Mac', 'Linux', 'Windows'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Which AI coding tool and subscription do you use?')
    .setHelpText('For example: Claude Code with Claude Pro, Cursor, ' +
      'Copilot through my institution, none yet.');

  const sheet = SpreadsheetApp.create(title + ' (responses)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Edit the form:   ' + form.getEditUrl());
  Logger.log('Fill-in link:    ' + form.getPublishedUrl());
  Logger.log('Responses Sheet: ' + sheet.getUrl());
  Logger.log('Check it with Preview, and click Publish if the form shows that button.');
}

function atMostTwo() {
  return FormApp.createCheckboxValidation()
    .setHelpText('Please pick at most two.')
    .requireSelectAtMost(2)
    .build();
}

function disableEmailCollection(form) {
  if (typeof form.setEmailCollectionType === 'function') {
    form.setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT);
  } else {
    form.setCollectEmail(false);
  }
}
