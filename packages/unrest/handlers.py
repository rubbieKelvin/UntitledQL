from . import templates
from typing import Callable, Any
from .exceptions import UnrestError
from rest_framework.request import Request
from .model import ModelConfig
from .config import UnrestAdapterBaseConfig
from .query import mapQ


class IntentHandler:
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
        self.name = name or handler.__name__
        self.description = description or handler.__doc__
        self.requiredArgs = set(requiredArgs) if requiredArgs else set()
        self.optionalArgs = set(optionalArgs) if optionalArgs else set()
        self.defaultValues = defaultValues or {}
        self.args = self.optionalArgs.union(self.requiredArgs)
        self.allowUnknownArgs = allowUnknownArgs
        self._handler = handler

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.name}({','.join([i for i in self.args])})"

    def __call__(
        self, request: Request, options: dict[str, Any]
    ) -> dict | list | tuple:
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

        # if we do mind foreign args, check if all arg in oprions was specified
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


class ModelIntentHandler:
    def __init__(
        self, rootConfig: UnrestAdapterBaseConfig, modelConfig: ModelConfig
    ) -> None:
        self.modelConfig = modelConfig
        self.rootConfig = rootConfig

    def select(self, request: Request, args: dict):
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        # get permission config
        # pass the user id here since we're trying to get the rows
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        try:
            Sr = self.modelConfig.createSerializerClass(role, "select")
        except PermissionError as e:
            raise UnrestError(
                templates.Error(
                    message=str(e),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        query = mapQ(args.get("where"))
        models = (
            self.modelConfig.model.objects.all()
            if permission.select.row == True
            else self.modelConfig.model.objects.filter(permission.select.row)
        )
        models = models.filter(query) if query else models

        return Sr(models, many=True).data

    @property
    def intenthandlers(self) -> dict[str, IntentHandler]:
        return {
            f"models.{self.modelConfig.name}.select": IntentHandler(
                self.select, optionalArgs=("where",)
            )
        }
