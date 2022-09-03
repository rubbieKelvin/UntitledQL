from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from django.http.response import HttpResponseBase
from django.db.models import Model

from . import templates

class UnrestAdapterBaseConfig():
    raise_exceptions = False
    models: dict[str, type[Model]] = {}
    functions = []

    def getAuthenticatedUserRoles(user:Model) -> str:
        """the calling function to get the role for a user"""
        raise NotImplementedError

def createUnrestAdapter(config: type[UnrestAdapterBaseConfig]) -> HttpResponseBase:
    def response_decorator(fn):
        def _(*args, **kwargs):

            try:
                res = fn(*args, **kwargs)
                if not res:
                    raise ValueError("intent did not return any data")
            except Exception as e:
                if config.raise_exceptions:
                    raise e
                res = templates.response(
                    error=templates.Error(
                        message=str(e),
                        type="INTERNAL_SERVER_ERROR",
                        code=500))

            return Response(
                res,
                status=res["meta"]["status_code"])
        return _
    
    # ...
    class UnrestAdapter(APIView):
        @response_decorator
        def post(self, request: Request) -> Response:
            body = request.data
            intent = body.get('intent')

            if intent == None:
                return templates.response(
                    data=None,
                    error=templates.Error(
                        message="intent not provided",
                        type="NO_INTENT"))

            return templates.response()
    
    return UnrestAdapter.as_view()