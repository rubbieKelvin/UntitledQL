import re

from uql.utils import templates as t
from uql.utils.exceptions import Interruption

from typing import Callable, Any
from typing_extensions import Self

from rest_framework.request import Request


def _validateModuleName(v: str) -> Self:
    modelc = re.compile(r"^(\w+[.]?\w+)$")
    if re.match(modelc, v):
        return v
    raise Exception(f"bad module name {v}")


def _validateFunctionName(v: str) -> Self:
    funcc = re.compile(r"^\w+$")
    if re.match(funcc, v):
        return v
    raise Exception(f"bad function name {v}")


class IntentFunction:
    def __init__(
        self,
        handler: Callable[[Request, dict[str, Any]], dict | list | tuple],
        name: str = None,
        description: str = None,
        requiredArgs: tuple = None,
        optionalArgs: tuple = None,
        defaultValues: dict = None,
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

    def __call__(
        self, request: Request, options: dict[str, Any]
    ) -> dict | list | tuple:
        # check if required args are present
        if not (self.requiredArgs.issubset(options.keys())):
            raise Interruption(
                t.error(
                    message=f'required keys "{self.requiredArgs.difference(options.keys())}" not given in argument',
                    code=400,
                    type="MISSING_REQUIRED_ARGS",
                )
            )

        # if required args have default argument, raise an error
        if self.defaultValues and set(self.defaultValues.keys()).issubset(
            self.requiredArgs
        ):
            raise Interruption(
                t.error(
                    message="required arguments should not have default values",
                    code=400,
                    type="DEFAULT_ON_REQUIRED_ARGS",
                )
            )

        # if we do mind foreign args, check if all arg in oprions was specified
        if not self.allowUnknownArgs and not set(options.keys()).issubset(self.args):
            raise Interruption(
                t.error(
                    message=f'unknown keys "{set(options.keys()).difference(self.args)}"',
                    code=400,
                    type="UNKNOWN_ARGS",
                )
            )

        for key, val in self.defaultValues.items():
            options.setdefault(key, val)

        return self._handler(request, options)


class IntentModule:
    def __init__(self, name: str, functions: list[IntentFunction]) -> None:
        self.name = _validateModuleName(name)
        self.functions = functions

    @property
    def spread(self) -> dict[str, IntentFunction]:
        return {f"{self.name}.{intent.name}": intent for intent in self.functions}
