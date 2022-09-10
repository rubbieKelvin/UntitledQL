from . import templates
from typing import Callable, Any
from .exceptions import UnrestError
from rest_framework.request import Request


class IntentHandler:
    def __init__(
        self,
        handler: Callable[[Request, dict[str, Any]], dict|list|tuple],
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
        self.name = name or handler.__name__
        self.description = description or handler.__doc__
        self.requiredArgs = set(requiredArgs) if requiredArgs else set()
        self.optionalArgs = set(optionalArgs) if optionalArgs else set()
        self.defaultValues = defaultValues or {}
        self.args = self.optionalArgs.union(self.requiredArgs)
        self.allowUnknownArgs = allowUnknownArgs
        self._handler = handler

    def __call__(self, request: Request, options: dict[str, Any]) -> dict|list|tuple:
        # check if required args are present
        if not (self.requiredArgs.issubset(options.keys())):
            raise UnrestError(
                templates.Error(
                    message=f'required keys "{self.requiredArgs.difference(options.keys())}" not given in argument',
                    code=400,
                    type="MISSING_REQUIRED_ARGS",
                )
            )

        # if required args have default argument, raise an error
        if self.defaultValues and set(self.defaultValues.keys()).issubset(
            self.requiredArgs
        ):
            raise UnrestError(
                templates.Error(
                    message="required arguments should not have default values",
                    code=400,
                    type="DEFAULT_ON_REQUIRED_ARGS",
                )
            )

        # if we do mind foriegn args, check if all arg in oprions was specified
        if not self.allowUnknownArgs and not set(options.keys()).issubset(self.args):
            raise UnrestError(
                templates.Error(
                    message=f'unknown keys "{set(options.keys()).difference(self.args)}"',
                    code=400,
                    type="UNKNOWN_ARGS",
                )
            )

        for key, val in self.defaultValues.items():
            options.setdefault(key, val)

        return self._handler(request, options)
