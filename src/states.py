from enum import Enum

class BotStates(str, Enum):
    READY = 'ready'
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    CONFUSED = 'confused'
    SLEEP = 'sleep'
