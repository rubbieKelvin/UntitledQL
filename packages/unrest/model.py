from django.db.models import Q, Model
from dataclasses import dataclass
from typing_extensions import Self


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


@dataclass(kw_only=True)
class ModelConfig:
    model: Model
    foriegnkeys: dict[str, Model] = None
    permissions: dict[str, ModelPermissionConfig] = None

    @property
    def name(self) -> str:
        return self.model._meta.verbose_name_plural
