from uql.constants.types import ErrorTyping


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
