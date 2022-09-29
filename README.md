# UntitledQL

Application layer for building Django apps with a breeze.

## Installation

⚠ project is still in development and things ~~might~~ will break

### Install using pip repo

```shell
pip install uql
```

### Install from git (recomended)

```shell
pip install git+https://github.com/rubbieKelvin/UntitledQL.git
```

## Usage

### Routing Setup

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

### Making requests

Uql manages calls via one endpoint, therefore different usecases would have to be handled some other way; I used `intents` to handle this.
Intents are basically strings/IDs that maps to a function. here's an example.

### UQL Response

### How Exceptions are handled

### Configuring models

### Using Permission

### Functions

### Model intents

### Multiple intents with one request

### Files

## Todo

- [ ] use CheckContraints for checks in input-update
- [ ] lookup permissions on functions
