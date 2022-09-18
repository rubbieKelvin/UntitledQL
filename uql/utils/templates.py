def error(*, message: str, type: str = "ERR_UNSPECIFIED", code: int = None):
    return dict(
        code=code,
        type=type,
        message=message,
    )


def response(
    data=None, error: dict = None, warning: str = None, code: int = 200, **meta
):
    return dict(
        meta={
            "has_error": error != None,
            "status_code": error.get("code", 400) if error else code,
            **meta,
        },
        data=data,
        error=error,
        warning=warning,
    )
