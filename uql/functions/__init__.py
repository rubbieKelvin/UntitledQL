import re
import typing

from uql import types
from uql.utils import dto

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
        rule: dto.Dictionary | None = None,
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
        self.rule = rule
        self._handler = handler

        # instantly name the root rule
        if self.rule:
            self.rule.name = "args"

    def toJson(self) -> dict:
        return {
            "name": self.name,
            "rule": None if self.rule == None else self.rule.toJson(),
            "description": self.description,
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        keys = [] if self.rule == None else self.rule.rules.keys()
        return f"{self.name}({','.join([i for i in keys])})"

    def __call__(
        self, request: Request, options: dict[str, typing.Any]
    ) -> types.IntentResult:
        if self.rule:
            self.rule.validate(options)

        return self._handler(request, options)

    @staticmethod
    def decorator(
        name: str | None = None,
        description: str | None = None,
        rule: dto.Dictionary | None = None,
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
                handler=handler, name=name, description=description, rule=rule
            )

        return _
