from typing import Sequence
from typing import Mapping
from typing import TypedDict


class ErrorTyping(TypedDict):
    message: str
    errorCode: int | str | None
    statusCode: int | None
    summary: str | None


def error(
    message: str,
    /,
    *,
    errorCode: int | str | None = None,
    statusCode: int | None = None,
    summary: str | None = None,
) -> ErrorTyping:
    return {
        "message": message,
        "errorCode": errorCode,
        "statusCode": statusCode,
        "summary": summary,
    }
