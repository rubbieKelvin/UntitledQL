from typing import Callable, Any
from uql.intent import IntentFunction
from rest_framework.request import Request


def intent(
    name: str = None,
    description: str = None,
    requiredArgs: tuple = None,
    optionalArgs: tuple = None,
    defaultValues: dict = None,
    allowUnknownArgs=False,
):
    def decorator(handler: Callable[[Request, dict[str, Any]], dict | list | tuple]):
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
