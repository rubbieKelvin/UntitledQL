from django.contrib import admin
from django.urls import path
from django.db.models import Q

from apps.main.models.users import User

from packages.unrest.model import ModelConfig
from packages.unrest.model import PermissionUnit
from packages.unrest.model import ModelPermissionConfig
from packages.unrest.adapter import createUnrestAdapter
from packages.unrest.adapter import UnrestAdapterBaseConfig


class Config(UnrestAdapterBaseConfig):
    raise_exceptions = True
    models = [
        ModelConfig(
            model=User,
            foriegnkeys=[],
            permissions={
                "anonymous": ModelPermissionConfig(
                    select=PermissionUnit(
                        row=Q(is_active=True),
                        column=[
                            "email",
                            "role",
                            "id",
                        ],
                    )
                )
            },
        )
    ]

    def getAuthenticatedUserRoles(user: User) -> str:
        return "anonymous" if user.is_anonymous else user.role


urlpatterns = [
    path("admin/", admin.site.urls),
    path("ur/", createUnrestAdapter(Config)),
]
