from typing import Callable, Any
from uql.constants import types
from uql.intent import IntentFunction
from rest_framework.request import Request


def intent(
    name: str | None = None,
    description: str | None = None,
    requiredArgs: tuple | None = None,
    optionalArgs: tuple | None = None,
    defaultValues: dict | None = None,
    allowUnknownArgs: bool = False,
):
    def decorator(handler: Callable[[Request, dict[str, Any]], types.IntentResult]):
        return IntentFunction(
            handler=handler,
            name=name,
            description=description,
            requiredArgs=requiredArgs,
            optionalArgs=optionalArgs,
            defaultValues=defaultValues,
            allowUnknownArgs=allowUnknownArgs,
        )

    return decorator
