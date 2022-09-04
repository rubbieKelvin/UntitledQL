from requests import post


class UnrestClient:
    def __init__(self) -> None:
        self.endpoint = "http://localhost:8000/ur/"

    def call(self, data: dict = None):
        response = post(self.endpoint, data=data)
        return response.text
