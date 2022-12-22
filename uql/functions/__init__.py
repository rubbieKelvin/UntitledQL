import re
import typing

from uql import types
from uql import constants
from uql.utils import templates as t
from uql.exceptions import RequestHandlingError

from rest_framework.request import Request


def _validateFunctionName(name: str) -> str:
    """This function checks if the given name is a valid function name by matching it
    against a regular expression that allows only alphanumeric characters and underscores.
    If the name is valid, it is returned.
    If the name is not valid, an exception is raised.

    Args:
        name (str): The name of the function.

    Returns:
        str: The validated function name.

    Raises:
        Exception: If the function name is invalid.
    """

    funcc = re.compile(r"^\w+$")
    if re.match(funcc, name):
        return name
    raise Exception(f"bad function name {name}")


class ApiFunction:
    def __init__(
        self,
        handler: typing.Callable[[Request, dict[str, typing.Any]], types.IntentResult],
        name: str | None = None,
        description: str | None = None,
        requiredArgs: tuple | None = None,
        optionalArgs: tuple | None = None,
        defaultValues: dict | None = None,
        allowUnknownArgs=False,
    ) -> None:
        """A function that can be called with a request and a dictionary of options as arguments.

        The function will first validate the given options by checking if all required arguments are
        present and that no default values are given for required arguments. It will also check if
        unknown arguments are present if the allowUnknownArgs flag is not set. If any of these checks
        fail, it will raise a RequestHandlingError with an appropriate error code and status code.
        If all checks pass, the function will set any default values for optional arguments that were
        not given and then call the handler function with the request and options as arguments and
        return the result.

        Args:
            handler (typing.Callable[[Request, dict[str, typing.Any]], dict|list|tuple]): The function
                to be called with the request and options as arguments.
            name (str, optional): The name of the function. Defaults to the name of the handler
                function.
            description (str, optional): A description of the function. Defaults to the docstring of the
                handler function.
            requiredArgs (tuple, optional): A tuple of required arguments for the function. Defaults to
                an empty tuple.
            optionalArgs (tuple, optional): A tuple of optional arguments for the function. Defaults to
                an empty tuple.
            defaultValues (dict, optional): A dictionary of default values for optional arguments.
                Defaults to an empty dictionary.
            allowUnknownArgs (bool, optional): A flag indicating if the function should allow unknown
                arguments in the options dictionary. Defaults to False.
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
        self, request: Request, options: dict[str, typing.Any]
    ) -> types.IntentResult:
        # check if required args are present
        if not (self.requiredArgs.issubset(options.keys())):
            raise RequestHandlingError(
                f'Required keys "{self.requiredArgs.difference(options.keys())}" not given in argument',
                errorCode=constants.MISSING_REQUIRED_ARGUMENT,
                statusCode=400,
            )

        # if required args have default argument, raise an error
        if self.defaultValues and set(self.defaultValues.keys()).issubset(
            self.requiredArgs
        ):
            raise RequestHandlingError(
                "Required arguments should not have default values",
                errorCode=constants.DEFAULT_ON_REQUIRED_ARGS,
                statusCode=500,
            )

        # if we do mind foreign args, check if all arg in oprions was specified
        if not self.allowUnknownArgs and not set(options.keys()).issubset(self.args):
            raise RequestHandlingError(
                f'Unknown keys "{set(options.keys()).difference(self.args)}"',
                errorCode=constants.UNKNOWN_ARGS,
                statusCode=400,
            )

        for key, val in self.defaultValues.items():
            options.setdefault(key, val)

        return self._handler(request, options)

    @staticmethod
    def decorator(
        name: str | None = None,
        description: str | None = None,
        requiredArgs: tuple | None = None,
        optionalArgs: tuple | None = None,
        defaultValues: dict | None = None,
        allowUnknownArgs: bool = False,
    ):
        """
        Decorator for defining and registering functions as "intents".

        This decorator takes the following arguments:

        name: str | None = None
        The name of the intent function. If not provided, the name of the decorated function will be used.

        description: str | None = None
        A description of the intent function. If not provided, the docstring of the decorated function will be used.

        requiredArgs: tuple | None = None
        A tuple of strings representing the required arguments for the intent function.

        optionalArgs: tuple | None = None
        A tuple of strings representing the optional arguments for the intent function.

        defaultValues: dict | None = None
        A dictionary of default values for the optional arguments of the intent function.

        allowUnknownArgs: bool = False
        A flag indicating whether the intent function can be called with arguments that were not specified in the requiredArgs or optionalArgs arguments.

        This decorator returns the decorated function wrapped in an ApiFunction object, which can be called like a regular function, but also has some additional properties and methods for handling input validation and other functionality."""

        def _(
            handler: typing.Callable[
                [Request, dict[str, typing.Any]], types.IntentResult
            ]
        ):
            return ApiFunction(
                handler=handler,
                name=name,
                description=description,
                requiredArgs=requiredArgs,
                optionalArgs=optionalArgs,
                defaultValues=defaultValues,
                allowUnknownArgs=allowUnknownArgs,
            )

        return _
