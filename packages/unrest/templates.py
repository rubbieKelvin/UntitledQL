from typing import Any


class Error:
    def __init__(self, message: str = "", type: str = "", code: int = None) -> None:
        self.message = message
        self.type = type
        self.code = code

    @property
    def json(self) -> dict:
        return dict(
            code=self.code,
            type=self.type,
            message=self.message,
        )


def response(data: Any = None, error: Error = None):
    return dict(
        meta={
            "has_error": bool(error),
            "status_code": (error.json["code"] or 400) if error else 200,
        },
        data=data,
        error=error.json if error else None,
    )
