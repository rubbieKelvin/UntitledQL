import typing
from typing_extensions import NotRequired

Pk: typing.TypeAlias = int | str

IntentResult: typing.TypeAlias = (
    typing.Mapping[str, typing.Any] | typing.Sequence[typing.Any] | None
)


class ErrorTyping(typing.TypedDict):
    message: str
    errorCode: int | str | None
    statusCode: int | None
    summary: str | None


class UQLRequestBodyTyping(typing.TypedDict):
    """Base structure for uql request input"""

    intent: str | None
    fields: bool | dict | None
    args: dict[str, typing.Any]


class UQLResponseBodyTyping(typing.TypedDict):
    data: typing.Mapping | typing.Sequence | None
    error: ErrorTyping | None
    warning: NotRequired[str | None]
    statusCode: int
