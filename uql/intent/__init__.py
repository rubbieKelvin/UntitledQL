import re
from uql.utils import templates as t
from uql.exceptions import RequestHandlingError
from uql.constants import errors as errorConstants
from typing import Callable, Any
from rest_framework.request import Request
from uql.constants import types


def _validateFunctionName(name: str) -> str:
    funcc = re.compile(r"^\w+$")
    if re.match(funcc, name):
        return name
    raise Exception(f"bad function name {name}")


class IntentFunction:
    def __init__(
        self,
        handler: Callable[[Request, dict[str, Any]], types.IntentResult],
        name: str | None = None,
        description: str | None = None,
        requiredArgs: tuple | None = None,
        optionalArgs: tuple | None = None,
        defaultValues: dict | None = None,
        allowUnknownArgs=False,
    ) -> None:
        """_summary_

        Args:
            handler (Callable[[Request, dict[str, Any]], dict|list|tuple]): _description_
            name (str, optional): _description_. Defaults to None.
            description (str, optional): _description_. Defaults to None.
            requiredArgs (tuple, optional): _description_. Defaults to None.
            optionalArgs (tuple, optional): _description_. Defaults to None.
            defaultValues (dict, optional): _description_. Defaults to None.
            allowUnknownArgs (bool, optional): _description_. Defaults to False.
        """
        self.name = _validateFunctionName(name or handler.__name__)
        self.description = description or handler.__doc__
        self.requiredArgs = set(requiredArgs) if requiredArgs else set()
        self.optionalArgs = set(optionalArgs) if optionalArgs else set()
        self.defaultValues = defaultValues or {}
        self.args = self.optionalArgs.union(self.requiredArgs)
        self.allowUnknownArgs = allowUnknownArgs
        self._handler = handler

    def json(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "requiredArgs": self.requiredArgs,
            "optionalArgs": self.optionalArgs,
            "defaultValues": self.defaultValues,
            "allowUnknownArgs": self.allowUnknownArgs,
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.name}({','.join([i for i in self.args])})"

    def __call__(self, request: Request, options: dict[str, Any]) -> types.IntentResult:
        # check if required args are present
        if not (self.requiredArgs.issubset(options.keys())):
            raise RequestHandlingError(
                f'Required keys "{self.requiredArgs.difference(options.keys())}" not given in argument',
                errorCode=errorConstants.MISSING_REQUIRED_ARGUMENT,
                statusCode=400,
            )

        # if required args have default argument, raise an error
        if self.defaultValues and set(self.defaultValues.keys()).issubset(
            self.requiredArgs
        ):
            raise RequestHandlingError(
                "Required arguments should not have default values",
                errorCode=errorConstants.DEFAULT_ON_REQUIRED_ARGS,
                statusCode=500,
            )

        # if we do mind foreign args, check if all arg in oprions was specified
        if not self.allowUnknownArgs and not set(options.keys()).issubset(self.args):
            raise RequestHandlingError(
                f'Unknown keys "{set(options.keys()).difference(self.args)}"',
                errorCode=errorConstants.UNKNOWN_ARGS,
                statusCode=400,
            )

        for key, val in self.defaultValues.items():
            options.setdefault(key, val)

        return self._handler(request, options)
