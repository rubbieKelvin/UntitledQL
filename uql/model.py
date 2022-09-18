from django.db.models import Q, Model
from django.db.models.fields import Field
from dataclasses import dataclass
from typing import Callable, Any
from typing_extensions import Self
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from .constants import RelationshipTypes, CellFlags


@dataclass(kw_only=True)
class ForeignKey:
    """data structure for foreign keys"""

    model: type[Model]
    type: RelationshipTypes


@dataclass(kw_only=True)
class PermissionUnit:
    """data structure for permission unit"""

    column: CellFlags | list[str]
    row: bool | Q


@dataclass(kw_only=True)
class InsertCheck:
    """a permission unit for insert operations.
    # check is a function that takes in request and the _set values to check if the values are valid
    """

    column: CellFlags | list[str]
    check: Callable[
        [Request, Any], bool
    ] = lambda req, _set: True  # takes in request and the attrs to set


@dataclass(kw_only=True)
class UpdateCheck:
    """a permission unit, for updates operations.
    # row is a query to get the list of updatable queryset
    # check is a function that takes in request and the _set values to check if the values are valid
    """

    column: CellFlags | list[str]
    row: bool | Q
    check: Callable[[Request, Any], bool] = lambda req, _set: True


@dataclass(kw_only=True)
class ModelPermissionConfig:
    """data stutructure for permission config"""

    select: PermissionUnit = None
    insert: InsertCheck = None
    update: UpdateCheck = None
    delete: PermissionUnit = None


class ModelConfig:
    modelConfigs = {}

    def __init__(
        self,
        *,
        model: type[Model],
        foreignKeys: dict[str, ForeignKey] = None,
        permissions: dict[str, Callable[[str | None], ModelPermissionConfig]] = None,
    ) -> None:
        self.model = model
        self.foreignKeys = foreignKeys or {}
        self.permissions = permissions or {}

        # add model configs
        # helpful to fetch configurations for feriegn keys
        # specified in other configurations
        # ------------------------------------------------
        # ? see self.getConfig
        self.modelConfigs[self.name] = self

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.name.title()} fk={self.foreignKeys}, perimissions={self.permissions}>"

    @property
    def name(self) -> str:
        """returns the name of the model.

        NOTE: i'm not sure if this would lead to conflicts in projects
            where there are similar model names in diffrent apps. if this happens to be
            a problem in the future, we might want to use Meta.label_lower.
        """
        return self.model._meta.model_name

    @staticmethod
    def getConfig(model: type[Model]) -> Self:
        """fetchs a model configuration if the model has been wrapped in the ModelConfig class.
        this should use the same method of model name generation used in ModelConfig.name
        """
        return ModelConfig.modelConfigs.get(model._meta.model_name)

    def createSerializerClass(
        self, role: str, parents: list[type[Model]] = None
    ) -> type[ModelSerializer]:
        """Creates a model serialiser class from user's role and operation type,
        which determines the kind of serializer that would be produced. depending on what
        data the user with `role` is permitted to access via self.permissions,
        certain data would be hidden. foreign keys will also be referred to in permissions
        if that model is registered in a ModelConfig class, the pemissions given to that model
        would apply to it's relationship.

        Args:
            role (str): the user's role
            parents (list[type[Model]], optional): list of all the models that's been called
                before this in linear manner, with each model traversing all the way up directly
                to it's parent. this is an effort to fix the infinte relationship loop, where a foreign model
                also referenced the parent model in it's serializer.

        Raises:
            TypeError: if the opration is invalid
            PermissionError: if the role is not sufficient for it's operation

        Returns:
            type[ModelSerializer]: returns the serializer class
        """
        parents = parents or []

        # get the permission from function. we do not need to pass the userid
        # as we only govern fetching columns here. we can simply pass None
        permission = self.permissions.get(role, lambda x: None)(None)
        operationObject: PermissionUnit = permission.select

        if not (permission and operationObject and operationObject.row):
            raise PermissionError(f'user with role "{role}" cannot select {self.name}')

        class Sr(ModelSerializer):
            class Meta:
                model = self.model
                # for the fields, we want to include all the specified
                # foreign keys along side the base fields.
                # setting fields to '__all__' isnt enough to fetch all specified fields from column,
                # hence this custom implementation.
                fields = (
                    [
                        field.name
                        for field in self.model._meta.get_fields()
                        if isinstance(field, Field)
                    ]
                    + [fk for fk in self.foreignKeys.keys()]
                    if operationObject.column == CellFlags.ALL_COLUMNS
                    else operationObject.column
                )

            def get_fields(cls):
                # get already defined fields from serializer class
                fields = super().get_fields()

                # create serializers for defined foreignkeys
                # and inject them into serializer fields
                for name, fk in self.foreignKeys.items():
                    if fk.model in parents:
                        # skip this model if it's been referenced somewhere
                        # from this node up from the parent's model root
                        continue

                    modelConfig: ModelConfig | None = ModelConfig.getConfig(fk.model)

                    if modelConfig:
                        _sr = modelConfig.createSerializerClass(
                            role, parents=[*parents, self.model]
                        )
                        fields[name] = _sr(many=fk.type == RelationshipTypes.LIST)
                return fields

        return Sr
