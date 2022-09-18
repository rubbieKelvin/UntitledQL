class Interruption(Exception):
    def __init__(self, errortemplate: dict) -> None:
        super().__init__(errortemplate.get("message", "an error occured"))
        self.errortemplate = errortemplate
