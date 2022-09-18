import os
from uql.intent import IntentFunction

def get_env(request, args):
    return os.environ

default = IntentFunction(get_env)