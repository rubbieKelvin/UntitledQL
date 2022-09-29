# UntitledQL

Application layer for building Django apps with a breeze.

## Installation

> ⚠ project is still in development and things ~~might~~ will break

### Install using pip repo

```shell
pip install uql
```

### Install from git (recomended)

```shell
pip install git+https://github.com/rubbieKelvin/UntitledQL.git
```

## Routing Setup

setup core configuration for routing. in your `urls.py`...

```python
from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction
from uql.views import UQLView

from django.contrib import admin
from django.urls import path
from django.contrib.auth.models import User # import user model

# define roles for permission
class CustomUserRoles:
    USER='user'
    ADMIN='admin'
    ANONYMOUS="anon"

class AppConfig(UQLConfig):
    raise_exceptions = True # raise errors instead of reporting them as data
    models: list[ModelConfig] = [] # list the models that should be configured for uql
    functions: list[IntentFunction] = [] # custom functions

    @staticmethod
    def getAuthenticatedUserRoles(user: User) -> str:
        """ This determines the roles when uql tries to figure out user permission. this method must be overwitten.
        """
        if user.is_anonymous:
            return CustomUserRoles.ANONYMOUS
        elif user.is_admin:
            return CustomUserRoles.ADMIN
        else:
            return CustomUserRoles.USER

urlpatterns = [
    path("admin/", admin.site.urls),
    path("uql/", UQLView(AppConfig).as_view())
]
```

now all your configured models and functions can be accessed via `host:port/uql`.

## Configuring models

Let's start with models and how we can work with them. Let's create a simple django model.

```python
from django.db import models

class Item(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=35)
    starred = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)
```

Now that we have a model, we need to expose the class to uql;

```python
from django.db.models import Q
from uql.model import ModelConfig
from uql.model import ModelPermissionConfig
from uql.model import SelectPermissionUnit

# ...

item_config = ModelConfig(
    model=Item, # our django model class
    permissions={
        # the roles we defined in AppConfig.getAuthenticatedUserRoles will be keys for permission object.
        CustomUserRoles.USER: lambda user_id: ModelPermissionConfig(
            # configures select access to CustomUserRoles.USER for this model
            select=SelectPermissionUnit(
                # specifies the rule for the rows that can be selected
                # Q(is_archived=False) specifies that only rows with Item.is_archived=False can be selected
                row=Q(is_archived=False),
                # specifies the columns that can be selected
                column=(
                    "id",
                    "name",
                    "starred",
                )
            )
        )
    }
)
```

## Making requests

Uql manages calls via one endpoint, therefore different usecases would have to be handled some other way; I used `intents` to handle this.
Intents are basically strings/IDs that maps to a function. All requests are made as `POST`.

> 🛈 Documentation in development

## UQL Response

...

## How Exceptions are handled

...

## Using Permission

...

## Functions

...

## Model intents

...

## Multiple intents with one request

...

## Files

...

## Testing

...

## Todo

- [ ] use CheckContraints for checks in input-update
- [ ] lookup permissions on functions
- [ ] Setup pagination
