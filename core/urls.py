from django.contrib import admin
from django.urls import path

from apps.main.models.users import User

from packages.unrest.adapter import createUnrestAdapter
from packages.unrest.adapter import UnrestAdapterBaseConfig

class Config(UnrestAdapterBaseConfig):
    raise_exceptions = True
    models = {
        "users": User
    }
    def getAuthenticatedUserRoles(user: User) -> str:
        return user.role

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ur/', createUnrestAdapter(Config))
]
