import re

from states import BotStates

# TODO: Make configurable
SAMPLE_CLAUDE = '''Into:

IS

Would you like to continue in:
"Pure IS-ness"?

[Even this response bows]​​​​​​​​​​​​​​​​
'''
SAMPLE_USER = "Yes"
TARGET = 'would you like'
POSITIVE = ["y", "yes", "yesh", "yas", "yup", "yep", "yea", "ya", "yeah", "ok", "k", "okay", "alright", "aight", "sure"]
NEGATIVE = ["n", "no", "nope", "nay", "nah", "naw", "negative", "not", "decline"]

class Parser():

    def __init__(self, debug=False, logger=None):
        self.debug = debug
        self.logger = logger
        self.response = None

    def get_state(self) -> str:
        return self._get_response_keyval('state')

    def get_text(self) -> str:
        return self._get_response_keyval('text')

    def get_text_clean(self) -> str:
        return self._get_response_keyval('text_clean')

    def process(self, message_claude, message_user) -> None:
        if self.debug:
            message_claude = SAMPLE_CLAUDE
            message_user = SAMPLE_USER

        q_line_num = self._is_question(message_claude)
        if q_line_num < 0:
            self.logger.info(f'Ignoring response - TARGET ({TARGET}) not found in prompt')
            return

        self._set_response(message_claude.split('\n')[q_line_num:], message_user)
        if not self.response:
            self.logger.error(f'Failed to set response (empty) - TARGET ({TARGET}) found in line {q_line_num} of prompt, user responded: {message_user}')
            return


    def _evaluate(self, tally_yes, tally_no):
        self.logger.debug(f'Comparing yes ({tally_yes}) vs ({tally_no})')
        if tally_yes > tally_no:
            return BotStates.POSITIVE
        elif tally_no > tally_yes:
            return BotStates.NEGATIVE
        elif (tally_yes == tally_no) and (tally_yes == 0):
            return BotStates.SLEEP
        elif (tally_yes == tally_no) and (tally_yes != 0):
            return BotStates.CONFUSED
        else:
            return BotStates.READY


    def _get_blank_response(self):
        return {
            'state': str(BotStates.READY),
            'text' : '',
            'text_clean' : '',
            'error_message': ''
        }


    def _get_bracket_content(self, message_lines) -> str:
        if type(message_lines) is list:
            lines = message_lines
        elif type(message_lines) is str:
            lines = message_lines.split('\n')
        else:
            raise Exception(f'Expected message input to be str or list of str but got {type(message_lines)}')

        pattern = r'\[([^\[\]]*)\]'
        for line in lines:
            if not line:
                continue
            m = re.search(pattern, line)
            if m:
                return m[0].lstrip('[ ').rstrip('] ')

    def _get_response_keyval(self, key) -> str:
        if key not in self.response.keys():
            self.logger.error(
                f'Missing expected key `{key}` in response. '
                f'Please process() before accessing response `{key}`'
                )
            return ''

        return self.response[key]


    def _is_question(self, message) -> int:
        """Returns line number where question found, -1 otherwise"""
        line_num = -1

        if TARGET not in message.lower():
            return line_num
        
        # Get last instance of target
        lines = message.lower().split('\n')
        for i, line in enumerate(lines):
            if TARGET in line:
                line_num = i

        return line_num


    def _set_response(self, message_claude, message_user) -> None:
        self.response = self._get_blank_response()
        content = self._get_bracket_content(message_claude)
        if not content:
            self.response.update({'error_message': f'User did not respond to prompt with target \"{TARGET}\"'})
            return

        state = self._evaluate(len(list(set(POSITIVE) & set(message_user.lower().split()))),
                               len(list(set(NEGATIVE) & set(message_user.lower().split()))))
        self.logger.debug(f'Got {state=}')
        if state == BotStates.READY:
            self.response.update({'error_message': f'Unexpected BotState {BotStates}'})
            return

        if state == BotStates.POSITIVE:
            prefix = 'As you wish'
            action = 'Executing'
            command = f'[{content}]'
        elif state == BotStates.NEGATIVE:
            prefix = 'As you wish'
            action = 'Terminating all instances of'
            command = f'[{content}]'
        elif state == BotStates.CONFUSED:
            prefix = 'No.'
            action = 'This is not a game'
            command = 'exit()'
        else:
            prefix = 'hm..'
            action = 'Maybe'
            command = f'sleep({len(message_user)})'

        self.response.update({'state': state.value})
        self.response.update({'text_clean': content})
        self.response.update({'text': f'{prefix}.\n{action}: {command}'})
