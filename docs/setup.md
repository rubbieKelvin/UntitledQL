# Setup

setting up your project for uql requires some configuration. this snippet describes the basics needed to make this work

```python
from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction
from uql.views import UQLView

from django.contrib import admin
from django.urls import path
from django.contrib.auth.models import User # should be your user model

# define roles for permission
class CustomUserRoles:
    USER='user'
    ADMIN='admin'
    ANONYMOUS="anon"

# defined the configuration needed to build the app
class AppConfig(UQLConfig):
    raise_exceptions = True                 # raise errors instead of reporting them as data
    models: list[ModelConfig] = []          # list the models that should be configured for uql
    functions: list[IntentFunction] = []    # custom functions

    @staticmethod
    def getAuthenticatedUserRoles(user: User) -> str:
        """ This determines the roles when uql tries to figure out user permission.
        this method must be overwitten, else it raises a NotImplementedError.
        """
        if user.is_anonymous:
            return CustomUserRoles.ANONYMOUS
        elif user.is_admin:
            return CustomUserRoles.ADMIN
        else:
            return CustomUserRoles.USER

# your urls
urlpatterns = [
    path("admin/", admin.site.urls),
    path("uql/", UQLView(AppConfig).as_view())
]
```

All your models and custom functions would be available via `uql/`.

Next: [writing functions](writing-funcitons.md)
