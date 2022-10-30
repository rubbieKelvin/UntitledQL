from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction


class UserRoles:
    USER = "user"
    ADMIN = "admin"
    ANON = "anonymous"


class Config(UQLConfig):
    raiseExceptions = False
    models: list[ModelConfig] = []
    functions: list[IntentFunction] = []

    @staticmethod
    def getAuthenticatedUserRoles(user) -> str:
        return UserRoles.ANON
