from .templates import Error


class UnrestError(Exception):
    def __init__(self, errortemplate: Error) -> None:
        super().__init__(errortemplate.message)
        self.errortemplate = errortemplate
