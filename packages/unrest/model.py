from django.db.models import Q, Model
from dataclasses import dataclass
from typing_extensions import Self
from rest_framework.serializers import ModelSerializer
from enum import Enum


class RelationshipTypes(Enum):
    LIST = 1
    OBJECT = 2


@dataclass(kw_only=True)
class ForeignKey:
    model: type[Model]
    type: RelationshipTypes


@dataclass(kw_only=True)
class PermissionUnit:
    column: str | list[str]
    row: bool | Q


@dataclass(kw_only=True)
class ModelPermissionConfig:
    select: PermissionUnit = None
    insert: PermissionUnit = None
    update: PermissionUnit = None
    delete: PermissionUnit = None


class ModelConfig:
    modelConfigs = {}

    def __init__(
        self,
        *,
        model: type[Model],
        foreignKeys: dict[str, ForeignKey] = None,
        permissions: dict[str, ModelPermissionConfig] = None,
    ) -> None:
        self.model = model
        self.foreignKeys = foreignKeys or {}
        self.permissions = permissions or {}

        # add model configs
        self.modelConfigs[self.name] = self

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.name.title()} fk={self.foreignKeys}, perimissions={self.permissions}>"

    @property
    def name(self) -> str:
        return self.model._meta.model_name

    @staticmethod
    def getConfig(model: type[Model]) -> Self:
        return ModelConfig.modelConfigs.get(model._meta.model_name)

    def createSerializerClass(self, role: str, operation: str) -> type[ModelSerializer]:
        """Creates a model serialiser class from user's role and operation type,
        which determines the kind of serializer that would be produced. depending on what
        data the user with `role` is permitted to access via self.permissions,
        certain data would be hidden. foreign keys will also be referred to in permissions
        if that model is registered in a ModelConfig class, the pemissions given to that model
        would apply to it's relationship.
        TODO: handle relationship loop

        Args:
            role (str): the user's role
            operation (str): any one of select|insert|update|delete

        Raises:
            TypeError: if the opration is invalid
            PermissionError: if the role is not sufficient for it's operation

        Returns:
            type[ModelSerializer]: returns the serializer class
        """
        if not (operation in ["select", "insert", "update", "delete"]):
            raise TypeError("invalid model operation")

        permission = self.permissions.get(role, None)
        operationObject: PermissionUnit = getattr(permission, operation)

        if not (permission or operation or operationObject.row):
            raise PermissionError(
                f'user with role "{role}" cannot access this {self.model._meta.model_name}'
            )

        class Sr(ModelSerializer):
            class Meta:
                model = self.model
                fields = operationObject.column

            def get_fields(cls):
                # get already defined fields from serializer class
                fields = super().get_fields()

                # create serializers for defined foreignkeys
                # and inject them into serilizer fields
                for name, fk in self.foreignKeys.items():
                    modelConfig: ModelConfig | None = ModelConfig.getConfig(fk.model)

                    if modelConfig:
                        _sr = modelConfig.createSerializerClass(role, operation)
                        fields[name] = _sr(many=fk.type == RelationshipTypes.LIST)
                return fields

        return Sr
