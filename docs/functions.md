# Writing funcitons

In uql you can write custom functions that's compactible with the one endpoint achitechure.

## Usage

### a function that returns current date and time

create a folder in `app/main/` called `functions`. all our functions will be kept in this folder. create a new script, in this case we'd be creating `myfunc.py`.
Then we create a function `getCurrentDateTime` that's decorated by `uql.decorators.intent.intent`.

> 🛈 intent function only returns `uql.constants.types.IntentResult`

```python
import typing
from datetime import datetime
from uql.decorators.intent import intent
from uql.constants.types import IntentResult
from rest_framework.request import Request


@intent()
def getCurrentDateTime(request: Request, args: dict[str, typing.Any]) -> IntentResult:
    now = datetime.now()
    return {
        "iso": now.isoformat(),
    }

```

Next we add this to our function list in `app/core/uqlc.py`

```python
# ...
from main.functions import myfunc

class Config(UQLConfig):
    # ...
    functions: list[IntentFunction] = [getTime.getCurrentDateTime]

```

At this point if we make a get request to our uql endpoint, we should get this:

```json
{
  "schema": {
    "functions.getCurrentDateTime": {
      "name": "functions.getCurrentDateTime",
      "description": null,
      "requiredArgs": [],
      "optionalArgs": [],
      "defaultValues": {},
      "allowUnknownArgs": false
    }
  }
}
```

This is a small description of the function we just passed, we can update the name, description and see the result

```python
# ...

@intent(name="datetime", description="returns current date time")
def getCurrentDateTime(request: Request, args: dict[str, typing.Any]) -> IntentResult:
    # ...
```

If we check our output we should see somthing similar to this:

```json
{
  "schema": {
    "functions.datetime": {
      "name": "functions.datetime",
      "description": "returns current date time",
      "requiredArgs": [],
      "optionalArgs": [],
      "defaultValues": {},
      "allowUnknownArgs": false
    }
  }
}
```

**Tip**: if you dont specify a description, uql will use the function's doc as description, like so:

```python
@intent()
def getCurrentDateTime(request: Request, args: dict[str, typing.Any]) -> IntentResult:
    """This function should return an the current datetime in iso format"""
    # ...
```

Our schema should look something like this:

```json
{
  "schema": {
    "functions.getCurrentDateTime": {
      "name": "functions.getCurrentDateTime",
      "description": "This function should return an the current datetime in iso format",
      "requiredArgs": [],
      "optionalArgs": [],
      "defaultValues": {},
      "allowUnknownArgs": false
    }
  }
}
```

## Calling functions from an API client

```bash
curl \
--location \
--request POST 'http://127.0.0.1:8000/uql/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "intent": "functions.getCurrentDateTime",
    "fields": true
}'
```

At the time of testing the output was:

```json
{
  "data": {
    "iso": "2022-10-30T12:44:35.122511"
  },
  "warning": null,
  "statusCode": 200,
  "error": null
}
```

UQL requests take in a few inputs (refer to `uql.constants.types.UQLRequestBodyTyping`):

- intent <str|None>
- fields <bool|dict|None>
- args dict<str, any>

### Intent

`intent` points uql to the resource the client is asking for, to call functions, the `functions.` prefix has to be appended to the function name. for example is we have a function that like so:

```python
@intent()
def myFunc(request, args):
  ...
```

it would we called as `functions.myFunc`. if the intent is explicitly named, the given name would take priority, example:

```python
@intent(name="notMyFunc")
def myFunc(request, args):
  ...
```

This would be identified as `functions.notMyFunc`.

### Fields

`fields` are prefered structured result. they can be bool, null or an object representing the actual result. If field is set to null, no data is returned. Example:

> 🛈 not passing fields yields the same result as setting it to null

```bash
curl \
--location \
--request POST 'http://127.0.0.1:8000/uql/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "intent": "functions.getCurrentDateTime",
    "fields": null
}'
```

the output would be:

```json
{
  "data": null,
  "warning": "fields not specified (or set to null), you might get an empty data",
  "statusCode": 200,
  "error": null
}
```

To understand fields better, let's say we have a function that return an object representing a single country. if we set fields=true, we get the raw data untouched.

```json
{
  "data": [
    {
      "name": {
        "common": "Barbados",
        "official": "Barbados",
        "nativeName": {
          "eng": {
            "official": "Barbados",
            "common": "Barbados"
          }
        }
      },
      "independent": true,
      "capital": ["Bridgetown"],
      "region": "Americas",
      "languages": {
        "eng": "English"
      },
      "timezones": ["UTC-04:00"],
      "flags": [
        {
          "type": "png",
          "url": "https://flagcdn.com/w320/bb.png"
        },
        {
          "type": "svg",
          "url": "https://flagcdn.com/bb.svg"
        }
      ]
    }
  ],
  "warning": null,
  "statusCode": 200,
  "error": null
}
```

If we set fields to false, we get nothing in the data:

```json
{
  "data": null,
  "warning": null,
  "statusCode": 200,
  "error": null
}
```

Now, suppose we only want the country's name, timezones and flag's url. we can pass something like this in our request body:

```json
{
  // ...
  "fields": {
    "name": {
      "official": true
    },
    "timezones": true,
    "flags": {
      "url": true
    }
  }
}
```

Our result would be streamlined to fit the description of the field:

```json
{
  "data": [
    {
      "name": {
        "official": "Barbados"
      },
      "timezones": ["UTC-04:00"],
      "flags": [
        {
          "url": "https://flagcdn.com/w320/bb.png"
        },
        {
          "url": "https://flagcdn.com/bb.svg"
        }
      ]
    }
  ],
  "warning": null,
  "statusCode": 200,
  "error": null
}
```

### Args

All arguments the function needs are passed as key value pairs
