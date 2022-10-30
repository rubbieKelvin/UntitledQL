import typing
from datetime import datetime
from uql.decorators.intent import intent
from uql.constants.types import IntentResult
from rest_framework.request import Request


@intent()
def getCurrentDateTime(request: Request, args: dict[str, typing.Any]) -> IntentResult:
    """This function should return an the current datetime in iso format"""
    now = datetime.now()
    return {
        "iso": now.isoformat(),
    }


@intent()
def getCountry(request: Request, args: dict[str, typing.Any]) -> IntentResult:
    """Returns an object representing Barbados"""
    return (
        {
            "name": {
                "common": "Barbados",
                "official": "Barbados",
                "nativeName": {"eng": {"official": "Barbados", "common": "Barbados"}},
            },
            "independent": True,
            "capital": ["Bridgetown"],
            "region": "Americas",
            "languages": {"eng": "English"},
            "timezones": ["UTC-04:00"],
            "flags": [
                {"type": "png", "url": "https://flagcdn.com/w320/bb.png"},
                {"type": "svg", "url": "https://flagcdn.com/bb.svg"},
            ],
        },
    )
