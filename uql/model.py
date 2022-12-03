from __future__ import annotations

from django.db.models import Q, Model
from django.db.models.fields import Field

from typing import Any
from typing import Callable
from typing import TypedDict
from typing import Literal
from typing import cast
from typing_extensions import NotRequired

from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer

from .constants import CellFlags
from .constants import ModelOperations
from .constants import types


class ForeignKeyTyping(TypedDict):
    """data structure for foreign keys"""

    model: type[Model]
    type: Literal["LIST"] | Literal["OBJECT"]


class SelectPermissionTyping(TypedDict):
    """data structure for permission unit"""

    column: CellFlags | list[str]  # these are the columns, permitted to be read
    row: CellFlags | Q  # queries the rows that could be read


class DeletePermissionTyping(TypedDict):
    row: CellFlags | Q  # queries the row that could be deleted


class InsertPermissionTyping(TypedDict):
    """a permission unit for insert operations.
    - check is a function that takes in request and the _set values to check if the values are valid
    """

    # the columns that are allowed to be inserted
    column: CellFlags | list[str]

    # the columns that must be inserted
    requiredFields: NotRequired[list[str]]

    # checks the data that's about to be inserted.
    # if false, insertion will not be permitted
    # - (request: Request, values: dict[str, any]) -> bool
    check: NotRequired[
        Callable[[Request, dict[str, Any]], bool]
    ]  # takes in request and the attrs to set


class PartialUpdateTyping(TypedDict):
    """This is the value passed to the update, updateMany intent ans on object to be updated.
    pk is the primary key of the row
    partial is the data that would be updated in the row

    Args:
        TypedDict (_type_): _description_
    """

    pk: types.Pk
    partial: dict[str, Any]


class UpdatePermissionTyping(TypedDict):
    """a permission unit, for updates operations.
    - row is a query to get the list of updatable queryset
    - check is a function that takes in request and the _set values to check if the values are valid
    """

    # the columns that could be updated
    column: CellFlags | list[str]

    # the possible rows that could be updated
    row: CellFlags | Q

    # checks the data that's about to be updated,
    # if it returns false, update will not be allowed
    # - (request: Request, partial: PartialUpdateTyping) -> bool
    check: NotRequired[Callable[[Request, PartialUpdateTyping], bool]]


class ModelPermissionTyping(TypedDict):
    """data stutructure for permission config"""

    select: NotRequired[SelectPermissionTyping | None]
    insert: NotRequired[InsertPermissionTyping | None]
    update: NotRequired[UpdatePermissionTyping | None]
    delete: NotRequired[DeletePermissionTyping | None]


class ModelConfig:
    modelConfigs: dict[str, ModelConfig] = {}

    def __init__(
        self,
        *,
        model: type[Model],
        foreignKeys: dict[str, ForeignKeyTyping] | None = None,
        permissions: dict[str, Callable[[types.Pk | None], ModelPermissionTyping]]
        | None = None,
        allowedOperations: list[ModelOperations] | None = None,
    ) -> None:
        self.model = model
        self.foreignKeys = foreignKeys or {}
        self.permissions = permissions or {}
        self.allowedOperations = allowedOperations or ModelOperations.all()

        # add model configs
        # helpful to fetch configurations for feriegn keys
        # specified in other configurations
        # ------------------------------------------------
        # ? see self.getConfig
        self.modelConfigs[self.name] = self

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.name.title()} fk={self.foreignKeys}, perimissions={self.permissions}>"

    @staticmethod
    def getModelName(model: type[Model]) -> str:
        return model._meta.label_lower

    @property
    def name(self) -> str:
        """returns the name of the model."""
        return self.getModelName(self.model)

    @staticmethod
    def getConfig(model: type[Model]) -> ModelConfig | None:
        """fetchs a model configuration if the model has been wrapped in the ModelConfig class.
        this should use the same method of model name generation used in ModelConfig.name
        """
        return ModelConfig.modelConfigs.get(ModelConfig.getModelName(model))

    def createSerializerClass(
        self, role: str, _parents: list[type[Model]] | None = None
    ) -> type[ModelSerializer]:
        """Creates a model serialiser class from user's role and operation type,
        which determines the kind of serializer that would be produced. depending on what
        data the user with `role` is permitted to access via self.permissions,
        certain data would be hidden. foreign keys will also be referred to in permissions
        if that model is registered in a ModelConfig class, the pemissions given to that model
        would apply to it's relationship.

        Args:
            role (str): the user's role
            _parents (list[type[Model]], optional): list of all the models that's been called
                before this in linear manner, with each model traversing all the way up directly
                to it's parent. this is an effort to fix the infinte relationship loop, where a foreign model
                also referenced the parent model in it's serializer.

        Raises:
            TypeError: if the opration is invalid
            PermissionError: if the role is not sufficient for it's operation

        Returns:
            type[ModelSerializer]: returns the serializer class
        """
        parents = _parents or []

        # get the permission from function. we do not need to pass the userid
        # as we only govern fetching columns here. we can simply pass None
        permission = self.permissions.get(role, lambda _: {})(None)
        selectPermission = permission.get("select")

        if not (
            permission
            and permission.get("select")
            and cast(SelectPermissionTyping, permission.get("select", {})).get("row")
        ):
            raise PermissionError(
                f'User with role: "{role}" cannot select {self.name}', 401
            )

        selectPermission = cast(SelectPermissionTyping, selectPermission)

        # refer to this instance
        config_instance = self

        class Sr(ModelSerializer):
            class Meta:
                model = config_instance.model
                # for the fields, we want to include all the specified
                # foreign keys along side the base fields.
                # setting fields to '__all__' isnt enough to fetch all specified fields from column,
                # hence this custom implementation.
                fields = (
                    [
                        field.name
                        for field in config_instance.model._meta.get_fields()
                        if isinstance(field, Field)
                    ]
                    + [fk for fk in config_instance.foreignKeys.keys()]
                    if selectPermission["column"] == CellFlags.ALL
                    else selectPermission["column"]
                )

            def get_fields(self, *args):
                # get already defined fields from serializer class
                fields = super().get_fields()

                # create serializers for defined foreignkeys
                # and inject them into serializer fields
                for name, fk in config_instance.foreignKeys.items():
                    if fk["model"] in parents:
                        # skip this model if it's been referenced somewhere
                        # from this node up from the parent's model root
                        continue

                    modelConfig: ModelConfig | None = ModelConfig.getConfig(fk["model"])

                    if modelConfig:
                        _sr = modelConfig.createSerializerClass(
                            role, _parents=[*parents, config_instance.model]
                        )
                        fields[name] = _sr(many=fk["type"] == "LIST")
                return fields

        return Sr


def fullPermissionAccess() -> ModelPermissionTyping:
    """returns a modelpermission that grants complete access to all model operations

    Returns:
        ModelPermissionTyping
    """
    return {
        "delete": {"row": CellFlags.ALL},
        "select": {"column": CellFlags.ALL, "row": CellFlags.ALL},
        "insert": {
            "column": CellFlags.ALL,
            "requiredFields": [],
            "check": lambda request, params: True,
        },
        "update": {"column": CellFlags.ALL, "row": CellFlags.ALL},
    }
