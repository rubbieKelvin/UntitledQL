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

    def createSerializerClass(
        self, role: str, operation: str, parents: list[type[Model]] = None
    ) -> type[ModelSerializer]:
        """Creates a model serialiser class from user's role and operation type,
        which determines the kind of serializer that would be produced. depending on what
        data the user with `role` is permitted to access via self.permissions,
        certain data would be hidden. foreign keys will also be referred to in permissions
        if that model is registered in a ModelConfig class, the pemissions given to that model
        would apply to it's relationship.

        Args:
            role (str): the user's role
            operation (str): any one of select|insert|update|delete
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
        if not (operation in ["select", "insert", "update", "delete"]):
            raise TypeError("invalid model operation")

        parents = parents or []
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
                # and inject them into serializer fields
                for name, fk in self.foreignKeys.items():
                    if fk.model in parents:
                        # skip this model if it's been referenced somewhere
                        # from this node up from the parent's model root
                        continue
                    
                    modelConfig: ModelConfig | None = ModelConfig.getConfig(fk.model)

                    if modelConfig:
                        _sr = modelConfig.createSerializerClass(
                            role, operation, parents=[*parents, self.model]
                        )
                        fields[name] = _sr(many=fk.type == RelationshipTypes.LIST)
                return fields

        return Sr
