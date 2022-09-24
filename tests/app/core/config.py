from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction, IntentModule

from main.models.users import User
from main.configs import users
from main.configs import notes
from main.functions import functions as fx


class Config(UQLConfig):
    raise_exceptions = True
    models: list[ModelConfig] = [
        users.default,
        notes.default,
    ]
    functions: list[IntentFunction | IntentModule] = fx

    @staticmethod
    def getAuthenticatedUserRoles(user: User) -> str:
        return "anonymous" if user.is_anonymous else user.role
