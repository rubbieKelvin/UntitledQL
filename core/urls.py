from django.contrib import admin
from django.urls import path
from django.db.models import Q

from apps.main.models.users import User
from apps.main.models.projects import Project

from packages.unrest.model import ForeignKey
from packages.unrest.model import ModelConfig
from packages.unrest.constants import RelationshipTypes, CellFlags
from packages.unrest.model import PermissionUnit
from packages.unrest.model import ModelPermissionConfig
from packages.unrest.adapter import createUnrestAdapter
from packages.unrest.config import UnrestAdapterBaseConfig


class Config(UnrestAdapterBaseConfig):
    raise_exceptions = True
    models = [
        ModelConfig(
            model=User,
            foreignKeys={
                "projects": ForeignKey(model=Project, type=RelationshipTypes.LIST)
            },
            permissions={
                "admin": lambda userID: ModelPermissionConfig(
                    select=PermissionUnit(row=True, column=CellFlags.ALL_COLUMNS),
                ),
                "anonymous": lambda _: ModelPermissionConfig(
                    select=PermissionUnit(
                        row=Q(
                            is_active=True,
                        ),
                        column=[
                            "email",
                            "role",
                            "id",
                            "projects",
                        ],
                    )
                ),
            },
        ),
        ModelConfig(
            model=Project,
            foreignKeys={
                "author": ForeignKey(model=User, type=RelationshipTypes.OBJECT)
            },
            permissions={
                "admin": lambda userID: ModelPermissionConfig(
                    select=PermissionUnit(
                        row=Q(author__id=userID), column=CellFlags.ALL_COLUMNS
                    ),
                ),
                "anonymous": lambda _: ModelPermissionConfig(
                    select=PermissionUnit(
                        row=Q(is_deleted=False),
                        column=[
                            "id",
                            "name",
                            "description",
                            "author",
                            "last_updated",
                            "is_archived",
                            "date_created",
                        ],
                    )
                ),
            },
        ),
    ]

    def getAuthenticatedUserRoles(user: User) -> str:
        return "anonymous" if user.is_anonymous else user.role


urlpatterns = [
    path("admin/", admin.site.urls),
    path("ur/", createUnrestAdapter(Config)),
]
