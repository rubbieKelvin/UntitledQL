class Anon:
    "mockup for anonymous user"
    is_anonymous = True

class Request:
    """mockup of rest_framework.request.Request"""
    def __init__(self, user=None, data:dict=None, method:str='post') -> None:
        self.user = user or Anon
        self.data = data or {}
        self.method = method
