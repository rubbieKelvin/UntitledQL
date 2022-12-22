import enum
import typing

from . import serializers
from django.db import models
from rest_framework.serializers import ModelSerializer

from uql import types
from uql import constants


def useFullPermissionAccess() -> types.ModelPermissionType:
    return {
        "delete": {"row": constants.ALL_ROWS},
        "select": {"column": constants.ALL_COLUMNS, "row": constants.ALL_ROWS},
        "insert": {
            "column": constants.ALL_COLUMNS,
            "check": lambda request, params: True,
        },
        "update": {"column": constants.ALL_COLUMNS, "row": constants.ALL_ROWS},
    }


class ExposedModel:
    __models: dict[str, "ExposedModel"] = {}

    ALL_COLUMNS = constants.ALL_COLUMNS
    ALL_ROWS = constants.ALL_ROWS

    def __init__(
        self,
        *,
        model: type[models.Model],
        operations: list[constants.ModelOperations] | None = None,
    ) -> None:
        self.model = model
        self.rolePermissions: dict[
            str, typing.Callable[[types.Pk | None], types.ModelPermissionType]
        ] = (
            {}
        )  # permission is a role:permissionObject container, keeps permission for each role
        self.operations = operations or constants.ModelOperations.all()

        # add model to dictionary
        self.__models[self.name] = self

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.name.title()}>"

    @staticmethod
    def getModelName(model: type[models.Model]) -> str:
        return model._meta.label_lower

    @staticmethod
    def createRolePermission(
        select: types.SelectPermissionType | None = None,
        insert: types.InsertPermissionType | None = None,
        update: types.UpdatePermissionType | None = None,
        delete: types.DeletePermissionType | None = None,
    ) -> types.ModelPermissionType:
        return {"select": select, "insert": insert, "update": update, "delete": delete}

    @staticmethod
    def getExposedModel(model: type[models.Model]) -> "ExposedModel":
        """fetchs a model configuration if the model has been wrapped in the ModelConfig class.
        this should use the same method of model name generation used in ModelConfig.name
        """
        return ExposedModel.__models[ExposedModel.getModelName(model)]

    @property
    def name(self) -> str:
        """returns the name of the exposed model"""
        return self.getModelName(self.model)

    def addPermission(
        self,
        role: str,
        perimission: typing.Callable[[types.Pk | None], types.ModelPermissionType],
    ) -> "ExposedModel":
        self.rolePermissions[role] = perimission
        return self

    def getSerializerClass(self, role: str) -> type[ModelSerializer]:
        return serializers.createSerializerClass(role, self)
