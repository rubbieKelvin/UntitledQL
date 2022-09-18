from __future__ import annotations
from .model import ModelConfig
from django.db.models import Model
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    # NOTE: only use these imports for typing
    # otherwise it results in an error
    from .intent import IntentFunction
    from .intent import IntentModule


class UQLConfig:
    raise_exceptions = True  # raise exception if an error occurs in intent handler
    models: list[ModelConfig] = []  # model configurations for unrest
    functions: list[IntentFunction|IntentModule] = []  # functions config for unrest

    @staticmethod
    def getAuthenticatedUserRoles(user: Model) -> str:
        """the calling function to get the role for a user"""
        # this method should be overriden
        raise NotImplementedError
