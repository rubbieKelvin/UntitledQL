from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction, IntentModule

from main.models.users import User
from main.configs import users
from main.configs import projects


class Config(UQLConfig):
    # raise_exceptions = False
    models: list[ModelConfig] = [
        users.default,
        projects.default,
    ]
    functions: list[IntentFunction | IntentModule] = []

    @staticmethod
    def getAuthenticatedUserRoles(user: User) -> str:
        return "anonymous" if user.is_anonymous else user.role
