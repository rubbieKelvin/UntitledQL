from . import templates
from typing import Callable, Any
from .exceptions import UnrestError
from rest_framework.request import Request
from .model import ModelConfig
from .config import UnrestAdapterBaseConfig
from .constants import CellFlags
from .query import mapQ
from django.db.models import Field


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
        """Select items of a model.

        Args:
            request (Request): _description_
            args (dict): _description_

        Raises:
            UnrestError: _description_

        Returns:
            _type_: _description_
        """
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        # get permission config
        # pass the user id here since we're trying to get the rows
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        try:
            Sr = self.modelConfig.createSerializerClass(role)
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

    def insert(self, request: Request, args: dict):
        _set: dict = args.get("_set")  # required

        # get role and permission config
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        # check permission's there
        # check insert's there
        # check that the _set values is valid

        _pass_check = False
        _has_insert_permission = permission and permission.insert

        if _has_insert_permission:
            _pass_check = permission.insert.check(request, _set)

        if not (_has_insert_permission and _pass_check):
            raise UnrestError(
                templates.Error(
                    message=(
                        "Unauthorized mutation"
                        if not _pass_check
                        else f'User with role "{role}" cannot insert into {self.modelConfig.name}'
                    ),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        # check if user only included permitted colums in _set
        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if permission.insert.column == CellFlags.ALL_COLUMNS
            else permission.insert.column
        )

        for key in _set.keys():
            if not (key in fields):
                raise UnrestError(
                    templates.Error(
                        message=f'cannot insert "{key}" in {self.modelConfig.name}',
                        type="UNKNOWN_KEYS",
                        code=400,
                    )
                )

        try:
            # create model
            model = self.modelConfig.model(**_set)
            model.save()

            # get model data from select realizers
            Sr = self.modelConfig.createSerializerClass(role)
            return Sr(model).data

        except Exception as e:
            raise UnrestError(
                templates.Error(
                    message=str(e),
                    type=e.__class__.__name__ or "UNKNOWN_ERROR",
                    code=400,
                )
            )

    @property
    def intenthandlers(self) -> dict[str, IntentHandler]:
        name = self.modelConfig.name

        return {
            f"models.{name}.select": IntentHandler(
                self.select, optionalArgs=("where",)
            ),
            f"models.{name}.insert": IntentHandler(self.insert, requiredArgs=("_set",)),
        }
