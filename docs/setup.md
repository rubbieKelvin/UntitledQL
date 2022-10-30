# Setup

## Starting a new django project

UQL is build firmly on django and djrf, so building a uql app is the same as building a django app. i'd go over from scratch so the complex parts are more welcoming.

```bash
mkdir app   # start off by creating you project folder
cd app  # move into project root
python -m venv venv # create virtual environment (you can skip this part)
source venv/bin/activate # activate virtual environment
pip install django django-rest-framework django-cors-headers # install dependencies
python -m django startproject core .    # create a django project in your root folder
```

You should have your project folder looking like so:

```
app
 +--core
 |   |--__init__.py
 |   |--asgi.py
 |   |--settings.py
 |   |--urls.py
 |   |--wsgi.py
 +--manage.py
```

Now we can go ahead and create a new app. we'd create an app called `main` in our project root

```bash
python manage.py startapp main
```

In your `settings.py` add the following to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken", # if you need to use auth implementation from djrf
    "main",
]
```

## Setting up uql

Setting up your project for uql requires some configuration, but first off, let's install uql.

> ⚠ project is still in development and things ~~might~~ will break

### Installing from pypi

```bash
pip install uql
```

### Installing from git repo

```bash
pip install git+https://github.com/rubbieKelvin/UntitledQL.git
# or pip install git+<link-to-your-fork>
```

### Configuration

Let's create a new file in `app/core/` called `uqlc.py` (you can name it anything actually), that's where all our configuration for uql with be. first thing we need to do in `uqlc.py`, is classify user roles. uql uses permission to correctly serve data meant for authorized groups.

```python
class UserRoles:
    USER = "user"
    ADMIN = "admin"
    ANON = "anonymous"
```

Now create a configuration class that inherits `uql.config.UQLConfig` (still in `uqlc.py`).

```python
from uql.config import UQLConfig
from uql.model import ModelConfig
from uql.intent import IntentFunction
from django.contrib.auth.models import User # should be your user model. else just use this

# ...

class Config(UQLConfig):
    raiseExceptions = False
    models: list[ModelConfig] = []
    functions: list[IntentFunction] = []

    @staticmethod
    def getAuthenticatedUserRoles(user) -> str:
        if user.is_anonymous:
            return CustomUserRoles.ANONYMOUS
        elif user.is_admin:
            return CustomUserRoles.ADMIN
        else:
            return CustomUserRoles.USER

```

- `UQLConfig.raiseExceptions` will raise exceptions instead of returning structured error message, which is very useful during debugging, but can be equally annoying.
- `UQLConfig.models` is a list of registered models. we'll understand how to set it up in a bit
- `UQLConfig.functions` is a list of registered functions. we'll be getting here soon
- `UQLConfig.getAuthenticatedUserRoles` defined how we get a user's role, it's used for permission handling and must be overwitten, else it raises a NotImplementedError

### Routing

Now that we're done with configuration, let's add uql to our url pattern in `app/core/urls.py`

```python
# Add uql imports
# ...
from uql.views import UQLView
from .uqlc import Config

# Add view to urls
urlpatterns = [
    # ...
    path('uql/', UQLView(Config).as_view()),
]
```

Run server and open the local link in the browser or postman, you should get this message:

```json
{
  "schema": null
}
```

Next: [writing functions](writing-funcitons.md)
